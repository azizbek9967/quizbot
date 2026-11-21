"""Create tables and insert/update sample trivia data. Safe to re-run (adds missing categories and questions)."""
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
        ("What is the powerhouse of the cell?", ["Nucleus", "Ribosome", "Mitochondria", "Endoplasmic Reticulum"], 2, "easy"),
    ]),
    "History": ("🏛️", [
        ("Who was the first President of the United States?", ["Thomas Jefferson", "John Adams", "George Washington", "Benjamin Franklin"], 2, "easy"),
        ("In which year did World War II end?", ["1943", "1945", "1947", "1950"], 1, "easy"),
        ("Which civilization built Machu Picchu?", ["Aztec", "Maya", "Inca", "Olmec"], 2, "medium"),
        ("In which year did the Berlin Wall fall?", ["1985", "1987", "1989", "1991"], 2, "medium"),
        ("Which 1648 treaties ended the Thirty Years' War?", ["Peace of Westphalia", "Treaty of Versailles", "Treaty of Utrecht", "Peace of Augsburg"], 0, "hard"),
        ("Who was the famous Carthaginian general who crossed the Alps with elephants?", ["Scipio", "Hannibal", "Julius Caesar", "Alexander"], 1, "medium"),
    ]),
    "Geography": ("🌍", [
        ("What is the capital of France?", ["Lyon", "Marseille", "Paris", "Nice"], 2, "easy"),
        ("Which is the largest ocean on Earth?", ["Atlantic", "Indian", "Arctic", "Pacific"], 3, "easy"),
        ("What is the longest river in Africa?", ["Congo", "Nile", "Niger", "Zambezi"], 1, "medium"),
        ("What is the capital of Australia?", ["Sydney", "Melbourne", "Canberra", "Perth"], 2, "medium"),
        ("Which country borders both the Caspian Sea and the Persian Gulf?", ["Iraq", "Turkey", "Iran", "Kazakhstan"], 2, "hard"),
        ("What is the smallest country in the world by area?", ["Monaco", "Liechtenstein", "Vatican City", "San Marino"], 2, "easy"),
    ]),
    "Technology": ("💻", [
        ("Who is widely considered the father of computers?", ["Alan Turing", "Charles Babbage", "Bill Gates", "Steve Jobs"], 1, "easy"),
        ("What does HTML stand for?", ["Hyper Text Markup Language", "High Tech Multi Language", "Hyperlink and Text Markup Language", "Home Tool Markup Language"], 0, "easy"),
        ("Which programming language was created by Guido van Rossum?", ["Java", "C++", "Python", "Ruby"], 2, "easy"),
        ("What does CPU stand for?", ["Central Process Unit", "Computer Personal Unit", "Central Processing Unit", "Central Processor Utility"], 2, "medium"),
        ("In what year was the first iPhone released?", ["2005", "2007", "2009", "2010"], 1, "medium"),
    ]),
    "Pop Culture": ("🎬", [
        ("Which movie features the quote 'May the Force be with you'?", ["Star Trek", "Star Wars", "Matrix", "Lord of the Rings"], 1, "easy"),
        ("Who wrote the Harry Potter book series?", ["J.R.R. Tolkien", "George R.R. Martin", "J.K. Rowling", "Stephen King"], 2, "easy"),
        ("Which band released the hit song 'Bohemian Rhapsody'?", ["The Beatles", "Led Zeppelin", "Queen", "Pink Floyd"], 2, "easy"),
        ("What is the highest-grossing film of all time (unadjusted for inflation)?", ["Titanic", "Avatar", "Avengers: Endgame", "Star Wars: The Force Awakens"], 1, "medium"),
    ]),
}


def main() -> None:
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        added_cats = 0
        added_qs = 0
        for name, (emoji, questions) in DATA.items():
            cat = session.scalar(select(Category).where(Category.name == name))
            if not cat:
                cat = Category(name=name, emoji=emoji)
                session.add(cat)
                session.flush()
                added_cats += 1

            existing_texts = {q.text for q in cat.questions}
            for t, c, i, d in questions:
                if t not in existing_texts:
                    session.add(Question(category_id=cat.id, text=t, choices=c, correct_index=i, difficulty=d))
                    added_qs += 1

        session.commit()
        print(f"Seed complete. Added {added_cats} new categories and {added_qs} new questions.")


if __name__ == "__main__":
    main()
