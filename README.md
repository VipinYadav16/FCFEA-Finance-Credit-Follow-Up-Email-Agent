# Finance Credit Follow-Up Email Agent

Workflow-first architecture for AI-assisted finance credit follow-up.

## Structure

- backend/: FastAPI app (API-first)
- frontend/: Streamlit UI
- data/: local data and SQLite db
- logs/: application logs

## Architecture (Step 2)

- API layer: FastAPI routes under backend/app/api
- Service layer: reusable business services under backend/app/services
- Database layer: SQLAlchemy models and sessions under backend/app/models and backend/app/db
- Utility layer: shared helpers under backend/app/utils

## Current Features

- Invoice domain models and validation
- CRUD endpoints for invoices
- Overdue calculations in API responses
- Audit log schema (future use)
- Streamlit invoice dashboard (API-driven)

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

## API Endpoints

- POST /invoices
- GET /invoices
- GET /invoices/{invoice_id}
- PUT /invoices/{invoice_id}
- DELETE /invoices/{invoice_id}

## Database Initialization

The SQLite database is created automatically on backend startup.

Optional seed data:

```bash
python backend/app/db/seed.py
```
