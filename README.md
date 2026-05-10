# Finance Credit Follow-Up Email Agent

Workflow-first architecture for AI-assisted finance credit follow-up.

## Structure

- backend/: FastAPI app (API-first)
- frontend/: Streamlit UI
- data/: local data and SQLite db
- logs/: application logs

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate the environment (Windows PowerShell):

```bash
venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy environment variables:

```bash
copy .env.example .env
```

## Run Backend

From the project root:

```bash
python -m uvicorn app.main:app --app-dir backend --reload
```

Health check:

```bash
http://localhost:8000/health
```

## Run Frontend

From the project root:

```bash
python -m streamlit run frontend/streamlit_app.py
```
