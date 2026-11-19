from sqlalchemy import JSON, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    emoji: Mapped[str] = mapped_column(String(8))

    questions: Mapped[list["Question"]] = relationship(back_populates="category")


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint("correct_index BETWEEN 0 AND 3", name="ck_correct_index"),
        CheckConstraint("difficulty IN ('easy','medium','hard')", name="ck_difficulty"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    text: Mapped[str] = mapped_column(String(500))
    choices: Mapped[list[str]] = mapped_column(JSON)  # exactly 4 strings
    correct_index: Mapped[int]
    difficulty: Mapped[str] = mapped_column(String(10))

    category: Mapped[Category] = relationship(back_populates="questions")
