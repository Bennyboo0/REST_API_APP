from datetime import datetime
import os
import re
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_ENDPOINT = os.getenv("DB_ENDPOINT")
DB_NAME = os.getenv("DB_NAME")
DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_ENDPOINT}/{DB_NAME}"


Base = declarative_base()


class GematriaWords(Base):
    __tablename__ = "gematria_words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String, nullable=False)
    normalized = Column(String, nullable=False, unique=True)
    gematria = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


def normalize(word: str) -> str:
    return re.sub(r'[^א-ת]', '', word)


gematria_values = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ך": 20, "ל": 30, "מ": 40, "ם": 40, "נ": 50, "ן": 50,
    "ס": 60, "ע": 70, "פ": 80, "ף": 80, "צ": 90, "ץ": 90,
    "ק": 100, "ר": 200, "ש": 300, "ת": 400,
}


def gematria_value(word: str) -> int:
    return sum(gematria_values[char] for char in word)


def main():
    engine = create_engine(DB_URL, echo=True)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    with session.begin(), open("words.txt") as file:
        for line in file:
            stripped_word = normalize(line)
            value = gematria_value(stripped_word)
            session.add(
                GematriaWords(
                    text=line.strip(),
                    normalized=stripped_word,
                    gematria=value)
            )
        session.commit()


if __name__ == "__main__":
    main()
