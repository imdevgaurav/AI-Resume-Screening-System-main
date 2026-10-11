from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import ScreeningResult


@dataclass
class ScoreBreakdown:
    skill_overlap_score: float
    text_similarity_score: float
    final_score: float
    matched_skills: list[str]
    missing_skills: list[str]


def calculate_text_similarity(job_text: str, resume_texts: list[str]) -> list[float]:
    if not job_text.strip() or not any(text.strip() for text in resume_texts):
        return [0.0 for _ in resume_texts]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([job_text, *resume_texts])
    similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    return [float(score) for score in similarities]


def calculate_skill_overlap(
    job_skills: list[str], resume_skills: list[str]
) -> tuple[float, list[str], list[str]]:
    job_skill_set = set(job_skills)
    resume_skill_set = set(resume_skills)

    matched = sorted(job_skill_set.intersection(resume_skill_set))
    missing = sorted(job_skill_set.difference(resume_skill_set))

    if not job_skill_set:
        return 0.0, matched, missing

    overlap = len(matched) / len(job_skill_set)
    return float(overlap), matched, missing


def build_scores(job_description, resumes, weights: dict[str, float]) -> list[ScoreBreakdown]:
    text_scores = calculate_text_similarity(
        job_description.cleaned_text, [resume.cleaned_text for resume in resumes]
    )

    results = []
    for resume, text_score in zip(resumes, text_scores):
        skill_score, matched, missing = calculate_skill_overlap(
            job_description.extracted_skills, resume.extracted_skills
        )
        final_score = weights["skills"] * skill_score + weights["text"] * text_score
        results.append(
            ScoreBreakdown(
                skill_overlap_score=round(skill_score, 4),
                text_similarity_score=round(text_score, 4),
                final_score=round(final_score, 4),
                matched_skills=matched,
                missing_skills=missing,
            )
        )

    return results


def create_screening_results(job_description, resumes, weights: dict[str, float]) -> list[ScreeningResult]:
    scored_results = build_scores(job_description, resumes, weights)
    ordered = sorted(
        zip(resumes, scored_results),
        key=lambda item: item[1].final_score,
        reverse=True,
    )

    screening_results = []
    for index, (resume, score) in enumerate(ordered, start=1):
        screening_results.append(
            ScreeningResult(
                job_description_id=job_description.id,
                resume_id=resume.id,
                skill_overlap_score=score.skill_overlap_score,
                text_similarity_score=score.text_similarity_score,
                final_score=score.final_score,
                matched_skills=score.matched_skills,
                missing_skills=score.missing_skills,
                rank=index,
            )
        )
    return screening_results
