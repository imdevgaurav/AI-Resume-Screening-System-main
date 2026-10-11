from app.services.screener import build_scores, calculate_text_similarity
from app.services.text_processing import TextProcessor


def test_clean_text_removes_common_noise():
    processor = TextProcessor("en_core_web_sm", "data/skills.json")
    cleaned = processor.clean_text("Python, Flask, and PostgreSQL are used in the system.")
    assert "python" in cleaned
    assert "flask" in cleaned
    assert "postgresql" in cleaned


def test_extract_skills_detects_known_terms():
    processor = TextProcessor("en_core_web_sm", "data/skills.json")
    skills = processor.extract_skills(
        "Built APIs with Python, Flask, PostgreSQL, spaCy, and scikit-learn."
    )
    assert {"python", "flask", "postgresql", "spacy", "scikit-learn"}.issubset(set(skills))


def test_text_similarity_returns_scores_for_each_resume():
    scores = calculate_text_similarity(
        "python flask postgresql nlp",
        ["python flask api", "react css frontend"],
    )
    assert len(scores) == 2
    assert scores[0] > scores[1]
    assert all(0.0 <= score <= 1.0 for score in scores)


def test_build_scores_combines_skill_and_text_scores():
    class Item:
        def __init__(self, cleaned_text, extracted_skills):
            self.cleaned_text = cleaned_text
            self.extracted_skills = extracted_skills

    job = Item("python flask postgresql nlp", ["python", "flask", "postgresql"])
    resumes = [
        Item("python flask api", ["python", "flask"]),
        Item("react css frontend", ["javascript"]),
    ]
    scores = build_scores(job, resumes, {"skills": 0.6, "text": 0.4})
    assert len(scores) == 2
    assert scores[0].final_score > scores[1].final_score
