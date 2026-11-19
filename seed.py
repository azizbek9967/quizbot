"""Create tables and insert sample trivia data. Safe to re-run (skips if data exists)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from db import engine
from models import Base, Category, Question

# category name -> (emoji, [(text, choices, correct_index, difficulty), ...])
DATA = {
    "Science": ("🔬", [
        ("What is the chemical symbol for gold?", ["Ag", "Au", "Gd", "Go"], 1, "easy"),
        ("Which planet is closest to the Sun?", ["Venus", "Earth", "Mercury", "Mars"], 2, "easy"),
        ("What is the most abundant gas in Earth's atmosphere?", ["Oxygen", "Nitrogen", "Carbon dioxide", "Argon"], 1, "medium"),
        ("Approximately how fast does light travel in a vacuum?", ["150,000 km/s", "300,000 km/s", "1,000,000 km/s", "30,000 km/s"], 1, "medium"),
        ("Which particle carries the strong force between quarks?", ["Photon", "Gluon", "Boson W", "Graviton"], 1, "hard"),
    ]),
    "History": ("🏛️", [
        ("Who was the first President of the United States?", ["Thomas Jefferson", "John Adams", "George Washington", "Benjamin Franklin"], 2, "easy"),
        ("In which year did World War II end?", ["1943", "1945", "1947", "1950"], 1, "easy"),
        ("Which civilization built Machu Picchu?", ["Aztec", "Maya", "Inca", "Olmec"], 2, "medium"),
        ("In which year did the Berlin Wall fall?", ["1985", "1987", "1989", "1991"], 2, "medium"),
        ("Which 1648 treaties ended the Thirty Years' War?", ["Peace of Westphalia", "Treaty of Versailles", "Treaty of Utrecht", "Peace of Augsburg"], 0, "hard"),
    ]),
    "Geography": ("🌍", [
        ("What is the capital of France?", ["Lyon", "Marseille", "Paris", "Nice"], 2, "easy"),
        ("Which is the largest ocean on Earth?", ["Atlantic", "Indian", "Arctic", "Pacific"], 3, "easy"),
        ("What is the longest river in Africa?", ["Congo", "Nile", "Niger", "Zambezi"], 1, "medium"),
        ("What is the capital of Australia?", ["Sydney", "Melbourne", "Canberra", "Perth"], 2, "medium"),
        ("Which country borders both the Caspian Sea and the Persian Gulf?", ["Iraq", "Turkey", "Iran", "Kazakhstan"], 2, "hard"),
    ]),
}


def main() -> None:
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        if session.scalar(select(Category).limit(1)):
            print("Data already present, nothing to do.")
            return
        for name, (emoji, questions) in DATA.items():
            cat = Category(name=name, emoji=emoji)
            cat.questions = [
                Question(text=t, choices=c, correct_index=i, difficulty=d)
                for t, c, i, d in questions
            ]
            session.add(cat)
        session.commit()
        print(f"Seeded {len(DATA)} categories and {sum(len(q) for _, q in DATA.values())} questions.")


if __name__ == "__main__":
    main()
