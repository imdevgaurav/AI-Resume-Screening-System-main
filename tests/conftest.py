from io import BytesIO
from pathlib import Path

import pytest

from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    UPLOAD_FOLDER = str(Path.cwd() / "test_uploads")
    SKILL_LEXICON_PATH = str(Path.cwd() / "data" / "skills.json")
    ALLOWED_EXTENSIONS = {"pdf", "txt"}
    SPACY_MODEL = "en_core_web_sm"
    FINAL_SCORE_WEIGHTS = {"skills": 0.6, "text": 0.4}


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_resume_file():
    content = (
        "Taylor Brown\n"
        "Python Engineer\n"
        "Experienced with Flask, PostgreSQL, spaCy, scikit-learn, SQL, and pytest."
    )
    return BytesIO(content.encode("utf-8"))
