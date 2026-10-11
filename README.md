# AI Resume Screening System

AI Resume Screening System is a portfolio-ready Flask application that parses resumes, extracts skills and keywords with NLP, compares them to a job description, and ranks candidates using a hybrid scoring approach.

## Features
- Upload one job description and multiple resumes
- Extract skills from resumes and job posts using spaCy phrase matching
- Generate keywords from cleaned text with TF-IDF
- Score candidates using a hybrid of skill overlap and text similarity
- Store jobs, resumes, and ranking results in SQL via SQLAlchemy
- Use PostgreSQL in production or SQLite for quick local development
- Access both server-rendered pages and JSON API endpoints

## Tech Stack
- Python
- Flask
- spaCy
- Scikit-learn
- SQLAlchemy
- PostgreSQL

## Project Structure
```text
app/
  services/
  static/
  templates/
data/
samples/
tests/
run.py
```

## Local Setup
1. Create a virtual environment and activate it.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and update values if needed.
4. Optional but recommended: install the spaCy English model:
   ```bash
   python -m spacy download en_core_web_sm
   ```
   The app still runs with a lightweight fallback tokenizer if the model is not installed.
5. Start the app:
   ```bash
   python run.py
   ```

The app will create the SQLite database automatically if `DATABASE_URL` is not set.

## PostgreSQL Example
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_screening
SECRET_KEY=replace-this
UPLOAD_FOLDER=uploads
SPACY_MODEL=en_core_web_sm
```

## SQLite Fallback Example
```env
SECRET_KEY=local-dev-secret
DATABASE_URL=sqlite:///resume_screening.db
UPLOAD_FOLDER=uploads
SPACY_MODEL=en_core_web_sm
```

## Sample Workflow
1. Create a job description from the dashboard or `POST /api/jobs`.
2. Upload multiple `.txt` or `.pdf` resumes from the dashboard or `POST /api/resumes/upload`.
3. Run the screening flow from the dashboard or `POST /api/screenings/run`.
4. Review ranked results on the UI or via `GET /api/screenings/<job_id>/results`.

## API Examples
Create a job:
```bash
curl -X POST http://127.0.0.1:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"Python NLP Engineer\", \"description\": \"Need Python, Flask, PostgreSQL, spaCy, and scikit-learn.\"}"
```

Upload resumes:
```bash
curl -X POST http://127.0.0.1:5000/api/resumes/upload \
  -F "resumes=@samples/resumes/alex_johnson.txt" \
  -F "resumes=@samples/resumes/sam_lee.txt"
```

Run screening:
```bash
curl -X POST http://127.0.0.1:5000/api/screenings/run \
  -H "Content-Type: application/json" \
  -d "{\"job_id\": 1}"
```

Get results:
```bash
curl http://127.0.0.1:5000/api/screenings/1/results
```

## Screenshots
- Add dashboard screenshot here
- Add ranking results screenshot here

## Sample Data
- `samples/job_description.txt`
- `samples/resumes/alex_johnson.txt`
- `samples/resumes/sam_lee.txt`

## Testing
Run:
```bash
pytest
```
