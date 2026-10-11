import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'resume_screening.db').as_posix()}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    SKILL_LEXICON_PATH = os.getenv(
        "SKILL_LEXICON_PATH", str(BASE_DIR / "data" / "skills.json")
    )
    ALLOWED_EXTENSIONS = {"pdf", "txt"}
    SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")
    FINAL_SCORE_WEIGHTS = {"skills": 0.6, "text": 0.4}
