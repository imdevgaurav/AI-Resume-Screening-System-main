from datetime import UTC, datetime

from app.extensions import db


def utcnow():
    return datetime.now(UTC)


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class JobDescription(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    cleaned_text = db.Column(db.Text, nullable=False)
    extracted_skills = db.Column(db.JSON, nullable=False, default=list)
    extracted_keywords = db.Column(db.JSON, nullable=False, default=list)

    screening_results = db.relationship(
        "ScreeningResult",
        back_populates="job_description",
        cascade="all, delete-orphan",
        lazy=True,
    )


class Resume(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_name = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    cleaned_text = db.Column(db.Text, nullable=False)
    extracted_skills = db.Column(db.JSON, nullable=False, default=list)
    extracted_keywords = db.Column(db.JSON, nullable=False, default=list)

    screening_results = db.relationship(
        "ScreeningResult",
        back_populates="resume",
        cascade="all, delete-orphan",
        lazy=True,
    )


class ScreeningResult(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_description_id = db.Column(
        db.Integer, db.ForeignKey("job_description.id"), nullable=False
    )
    resume_id = db.Column(db.Integer, db.ForeignKey("resume.id"), nullable=False)
    skill_overlap_score = db.Column(db.Float, nullable=False)
    text_similarity_score = db.Column(db.Float, nullable=False)
    final_score = db.Column(db.Float, nullable=False)
    matched_skills = db.Column(db.JSON, nullable=False, default=list)
    missing_skills = db.Column(db.JSON, nullable=False, default=list)
    rank = db.Column(db.Integer, nullable=False)

    job_description = db.relationship("JobDescription", back_populates="screening_results")
    resume = db.relationship("Resume", back_populates="screening_results")
