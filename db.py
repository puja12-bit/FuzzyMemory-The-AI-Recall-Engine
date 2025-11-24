# db.py
import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "fuzzy_memory.db")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class ContentItem(Base):
    """
    Generic content item in FuzzyMemory.
    type: song, dialogue, quote, etc.
    """
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), index=True)       # 'song', 'dialogue', 'quote', etc.
    title = Column(String(255), index=True)
    creator = Column(String(255), index=True)   # artist / author / speaker
    context = Column(Text)                      # description, tags, free text
    metadata_json = Column(Text)                # JSON: youtube_search, derivatives, etc.


def init_db_and_seed():
    """
    Create tables and seed from seed_data.json if DB is empty.
    Runs at container startup inside Cloud Run.
    """
    Base.metadata.create_all(bind=engine)

    from sqlalchemy.orm import Session
    db: Session = SessionLocal()
    try:
        # check if already seeded
        existing = db.query(ContentItem).count()
        if existing > 0:
            return

        seed_path = os.path.join(BASE_DIR, "seed_data.json")
        if not os.path.exists(seed_path):
            print("seed_data.json not found, skipping seed.")
            return

        with open(seed_path, "r", encoding="utf-8") as f:
            seed = json.load(f)

        for entry in seed:
            if entry.get("semitones"):
                ctype = "song"
            elif entry.get("said_by"):
                ctype = "dialogue"
            else:
                ctype = "generic"

            title = entry.get("title", "")
            creator = entry.get("artist") or entry.get("said_by") or ""
            context_list = entry.get("context") or []
            context_text = "; ".join(context_list)

            metadata = {
                "youtube_search": entry.get("youtube_search", ""),
                "derivatives": entry.get("derivatives", []),
                "raw": entry,
            }

            item = ContentItem(
                type=ctype,
                title=title,
                creator=creator,
                context=context_text,
                metadata_json=json.dumps(metadata),
            )
            db.add(item)

        db.commit()
        print(f"Seeded {len(seed)} items into fuzzy_memory.db")
    finally:
        db.close()
