from app.models import Resume


def test_create_job_and_upload_resume(client, sample_resume_file):
    response = client.post(
        "/api/jobs",
        json={
            "title": "Python NLP Engineer",
            "description": "Need Python, Flask, PostgreSQL, spaCy, and scikit-learn.",
        },
    )
    assert response.status_code == 201
    job_id = response.get_json()["id"]

    upload_response = client.post(
        "/api/resumes/upload",
        data={"resumes": (sample_resume_file, "taylor_brown.txt")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 201
    payload = upload_response.get_json()
    assert len(payload["uploaded"]) == 1

    screening_response = client.post("/api/screenings/run", json={"job_id": job_id})
    assert screening_response.status_code == 201

    result_response = client.get(f"/api/screenings/{job_id}/results")
    result_payload = result_response.get_json()
    assert result_response.status_code == 200
    assert result_payload["results"][0]["candidate_name"] == "Taylor Brown"
    assert result_payload["results"][0]["rank"] == 1


def test_resume_detail_api_returns_extracted_data(app, client, sample_resume_file):
    client.post(
        "/api/resumes/upload",
        data={"resumes": (sample_resume_file, "taylor_brown.txt")},
        content_type="multipart/form-data",
    )

    with app.app_context():
        resume = Resume.query.first()
    response = client.get(f"/api/resumes/{resume.id}")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["candidate_name"] == "Taylor Brown"
    assert "python" in payload["skills"]
