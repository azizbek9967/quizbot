from fastapi import FastAPI, HTTPException
from sqlalchemy import text, select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from db import engine
from models import Base, Question

app = FastAPI(title="Health API")


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
