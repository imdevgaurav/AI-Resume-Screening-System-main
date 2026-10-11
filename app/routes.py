from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from app.extensions import db
from app.models import JobDescription, Resume, ScreeningResult
from app.services.file_parser import FileParserError, allowed_file, extract_text
from app.services.screener import create_screening_results
from app.services.text_processing import TextProcessor


main_bp = Blueprint("main", __name__)


def get_text_processor() -> TextProcessor:
    return TextProcessor(
        current_app.config["SPACY_MODEL"],
        current_app.config["SKILL_LEXICON_PATH"],
    )


@main_bp.route("/", methods=["GET"])
def dashboard():
    jobs = JobDescription.query.order_by(JobDescription.created_at.desc()).all()
    resumes = Resume.query.order_by(Resume.created_at.desc()).all()
    latest_job = jobs[0] if jobs else None
    latest_results = []
    if latest_job:
        latest_results = (
            ScreeningResult.query.filter_by(job_description_id=latest_job.id)
            .order_by(ScreeningResult.rank.asc())
            .all()
        )
    return render_template(
        "dashboard.html",
        jobs=jobs,
        resumes=resumes,
        latest_job=latest_job,
        latest_results=latest_results,
    )


@main_bp.route("/jobs", methods=["POST"])
def create_job():
    title = request.form.get("title", "").strip()
    raw_text = request.form.get("description", "").strip()

    if not title or not raw_text:
        flash("Job title and description are required.", "error")
        return redirect(url_for("main.dashboard"))

    processor = get_text_processor()
    cleaned_text = processor.clean_text(raw_text)
    if not cleaned_text:
        flash("Job description must contain extractable text.", "error")
        return redirect(url_for("main.dashboard"))

    job = JobDescription(
        title=title,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        extracted_skills=processor.extract_skills(raw_text),
        extracted_keywords=processor.extract_keywords(raw_text),
    )
    db.session.add(job)
    db.session.commit()

    flash("Job description created.", "success")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/resumes/upload", methods=["POST"])
def upload_resumes():
    files = request.files.getlist("resumes")
    if not files:
        flash("Upload at least one resume.", "error")
        return redirect(url_for("main.dashboard"))

    processor = get_text_processor()
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    successes = 0
    failures = []

    for file in files:
        if not file or not file.filename:
            failures.append("One upload was empty.")
            continue

        if not allowed_file(file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
            failures.append(f"{file.filename}: unsupported file type.")
            continue

        safe_name = f"{uuid4().hex}_{Path(file.filename).name}"
        target_path = upload_dir / safe_name
        file.save(target_path)

        try:
            raw_text = extract_text(str(target_path))
            cleaned_text = processor.clean_text(raw_text)
            if not cleaned_text:
                raise FileParserError("No extractable text found.")

            resume = Resume(
                candidate_name=processor.detect_candidate_name(raw_text, file.filename),
                original_filename=file.filename,
                file_path=str(target_path),
                raw_text=raw_text,
                cleaned_text=cleaned_text,
                extracted_skills=processor.extract_skills(raw_text),
                extracted_keywords=processor.extract_keywords(raw_text),
            )
            db.session.add(resume)
            successes += 1
        except FileParserError as exc:
            failures.append(f"{file.filename}: {exc}")
            target_path.unlink(missing_ok=True)

    db.session.commit()

    if successes:
        flash(f"Uploaded {successes} resume(s).", "success")
    for failure in failures:
        flash(failure, "error")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/screenings/run", methods=["POST"])
def run_screening():
    job_id = request.form.get("job_id", type=int)
    if not job_id:
        flash("Select a job description.", "error")
        return redirect(url_for("main.dashboard"))

    job = JobDescription.query.get_or_404(job_id)
    resumes = Resume.query.order_by(Resume.created_at.desc()).all()

    if not resumes:
        flash("Upload resumes before running screening.", "error")
        return redirect(url_for("main.dashboard"))

    ScreeningResult.query.filter_by(job_description_id=job.id).delete()
    db.session.flush()

    screening_results = create_screening_results(
        job, resumes, current_app.config["FINAL_SCORE_WEIGHTS"]
    )
    db.session.add_all(screening_results)
    db.session.commit()

    flash("Screening completed.", "success")
    return redirect(url_for("main.screening_results_page", job_id=job.id))


@main_bp.route("/results/<int:job_id>", methods=["GET"])
def screening_results_page(job_id: int):
    job = JobDescription.query.get_or_404(job_id)
    results = (
        ScreeningResult.query.filter_by(job_description_id=job.id)
        .order_by(ScreeningResult.rank.asc())
        .all()
    )
    return render_template("results.html", job=job, results=results)


@main_bp.route("/resumes/<int:resume_id>", methods=["GET"])
def resume_detail(resume_id: int):
    resume = Resume.query.get_or_404(resume_id)
    results = (
        ScreeningResult.query.filter_by(resume_id=resume.id)
        .order_by(ScreeningResult.final_score.desc())
        .all()
    )
    return render_template("resume_detail.html", resume=resume, results=results)


@main_bp.route("/api/jobs", methods=["POST"])
def api_create_job():
    payload = request.get_json(silent=True) or request.form
    title = (payload.get("title") or "").strip()
    raw_text = (payload.get("description") or "").strip()

    if not title or not raw_text:
        return jsonify({"error": "title and description are required"}), 400

    processor = get_text_processor()
    cleaned_text = processor.clean_text(raw_text)
    if not cleaned_text:
        return jsonify({"error": "description must contain extractable text"}), 400

    job = JobDescription(
        title=title,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        extracted_skills=processor.extract_skills(raw_text),
        extracted_keywords=processor.extract_keywords(raw_text),
    )
    db.session.add(job)
    db.session.commit()

    return (
        jsonify(
            {
                "id": job.id,
                "title": job.title,
                "extracted_skills": job.extracted_skills,
                "extracted_keywords": job.extracted_keywords,
            }
        ),
        201,
    )


@main_bp.route("/api/resumes/upload", methods=["POST"])
def api_upload_resumes():
    files = request.files.getlist("resumes")
    if not files:
        return jsonify({"error": "at least one resume file is required"}), 400

    processor = get_text_processor()
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    uploaded = []
    errors = []

    for file in files:
        if not file or not file.filename:
            errors.append({"filename": "", "error": "empty upload"})
            continue

        if not allowed_file(file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
            errors.append({"filename": file.filename, "error": "unsupported file type"})
            continue

        safe_name = f"{uuid4().hex}_{Path(file.filename).name}"
        target_path = upload_dir / safe_name
        file.save(target_path)

        try:
            raw_text = extract_text(str(target_path))
            cleaned_text = processor.clean_text(raw_text)
            if not cleaned_text:
                raise FileParserError("no extractable text found")

            resume = Resume(
                candidate_name=processor.detect_candidate_name(raw_text, file.filename),
                original_filename=file.filename,
                file_path=str(target_path),
                raw_text=raw_text,
                cleaned_text=cleaned_text,
                extracted_skills=processor.extract_skills(raw_text),
                extracted_keywords=processor.extract_keywords(raw_text),
            )
            db.session.add(resume)
            db.session.flush()
            uploaded.append(
                {
                    "id": resume.id,
                    "candidate_name": resume.candidate_name,
                    "filename": resume.original_filename,
                    "skills": resume.extracted_skills,
                }
            )
        except FileParserError as exc:
            errors.append({"filename": file.filename, "error": str(exc)})
            target_path.unlink(missing_ok=True)

    db.session.commit()
    status = 201 if uploaded else 400
    return jsonify({"uploaded": uploaded, "errors": errors}), status


@main_bp.route("/api/screenings/run", methods=["POST"])
def api_run_screening():
    payload = request.get_json(silent=True) or request.form
    raw_job_id = payload.get("job_id") if hasattr(payload, "get") else None
    try:
        job_id = int(raw_job_id)
    except (TypeError, ValueError):
        job_id = None
    if not job_id:
        return jsonify({"error": "job_id is required"}), 400

    job = db.session.get(JobDescription, job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404

    resumes = Resume.query.order_by(Resume.created_at.desc()).all()
    if not resumes:
        return jsonify({"error": "no resumes available"}), 400

    ScreeningResult.query.filter_by(job_description_id=job.id).delete()
    db.session.flush()

    results = create_screening_results(job, resumes, current_app.config["FINAL_SCORE_WEIGHTS"])
    db.session.add_all(results)
    db.session.commit()

    return jsonify({"job_id": job.id, "screened_count": len(results)}), 201


@main_bp.route("/api/screenings/<int:job_id>/results", methods=["GET"])
def api_screening_results(job_id: int):
    job = db.session.get(JobDescription, job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404

    results = (
        ScreeningResult.query.filter_by(job_description_id=job.id)
        .order_by(ScreeningResult.rank.asc())
        .all()
    )
    return jsonify(
        {
            "job": {"id": job.id, "title": job.title},
            "results": [
                {
                    "rank": result.rank,
                    "resume_id": result.resume.id,
                    "candidate_name": result.resume.candidate_name,
                    "final_score": result.final_score,
                    "skill_overlap_score": result.skill_overlap_score,
                    "text_similarity_score": result.text_similarity_score,
                    "matched_skills": result.matched_skills,
                    "missing_skills": result.missing_skills,
                }
                for result in results
            ],
        }
    )


@main_bp.route("/api/resumes/<int:resume_id>", methods=["GET"])
def api_resume_detail(resume_id: int):
    resume = db.session.get(Resume, resume_id)
    if not resume:
        return jsonify({"error": "resume not found"}), 404

    return jsonify(
        {
            "id": resume.id,
            "candidate_name": resume.candidate_name,
            "filename": resume.original_filename,
            "skills": resume.extracted_skills,
            "keywords": resume.extracted_keywords,
            "raw_text": resume.raw_text,
        }
    )
