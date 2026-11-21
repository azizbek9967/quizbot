from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text, select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from db import engine
from models import Base, Category, Question

app = FastAPI(title="Quiz API")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail={"status": "error", "database": "unreachable"})
    return {"status": "ok", "database": "connected"}


@app.get("/questions/random")
def get_random_question():
    try:
        with Session(engine) as session:
            question = session.scalars(select(Question).order_by(func.random())).first()
            if not question:
                raise HTTPException(status_code=404, detail="No questions found")
            return {
                "id": question.id,
                "category_id": question.category_id,
                "text": question.text,
                "choices": question.choices,
                "correct_index": question.correct_index,
                "difficulty": question.difficulty,
            }
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail={"status": "error", "database": "unreachable"})


class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=100)
    emoji: str = Field(..., max_length=8)


class QuestionCreate(BaseModel):
    category_id: int | None = None
    category_name: str | None = None
    text: str = Field(..., max_length=500)
    choices: list[str] = Field(..., min_length=4, max_length=4)
    correct_index: int = Field(..., ge=0, le=3)
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")


@app.post("/categories")
def create_category(payload: CategoryCreate):
    try:
        with Session(engine) as session:
            existing = session.scalar(select(Category).where(Category.name == payload.name))
            if existing:
                raise HTTPException(status_code=400, detail="Category already exists")
            cat = Category(name=payload.name, emoji=payload.emoji)
            session.add(cat)
            session.commit()
            session.refresh(cat)
            return {"id": cat.id, "name": cat.name, "emoji": cat.emoji}
    except SQLAlchemyError as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=503, detail={"status": "error", "database": "unreachable"})


@app.post("/questions")
def create_question(payload: QuestionCreate):
    try:
        with Session(engine) as session:
            cat_id = payload.category_id
            if not cat_id and payload.category_name:
                cat = session.scalar(select(Category).where(Category.name == payload.category_name))
                if not cat:
                    raise HTTPException(status_code=404, detail=f"Category '{payload.category_name}' not found")
                cat_id = cat.id
            elif not cat_id:
                raise HTTPException(status_code=400, detail="Either category_id or category_name must be provided")

            cat = session.get(Category, cat_id)
            if not cat:
                raise HTTPException(status_code=404, detail="Category not found")

            q = Question(
                category_id=cat_id,
                text=payload.text,
                choices=payload.choices,
                correct_index=payload.correct_index,
                difficulty=payload.difficulty,
            )
            session.add(q)
            session.commit()
            session.refresh(q)
            return {
                "id": q.id,
                "category_id": q.category_id,
                "text": q.text,
                "choices": q.choices,
                "correct_index": q.correct_index,
                "difficulty": q.difficulty,
            }
    except SQLAlchemyError as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=503, detail={"status": "error", "database": "unreachable"})
