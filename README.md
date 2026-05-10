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
- Audit log access for workflow events
- Deterministic workflow engine for escalation staging
- Streamlit workflow dashboard (API-driven)

## Workflow Engine (Step 3)

Deterministic escalation staging is calculated from invoice overdue days. The workflow engine updates
`current_stage` and writes audit logs for stage transitions.

Escalation rules:

- 1-7 days overdue: STAGE_1
- 8-14 days overdue: STAGE_2
- 15-21 days overdue: STAGE_3
- 22-30 days overdue: STAGE_4
- 31+ days overdue: LEGAL_ESCALATION

Workflow processing flow:

1. Fetch invoices ordered by due date.
2. Skip non-overdue invoices.
3. Determine escalation stage from overdue days.
4. Update stage only when it changes.
5. Write audit log entries for stage transitions.

Observability highlights:

- Workflow run summary returns processed, updated, skipped, error, overdue, escalated, and legal counts.
- Stage distribution returned in `stage_counts` for quick dashboard validation.
- Logs emit run start, per-escalation transitions, and run completion metrics.

Audit logging structure:

- `action_type`: `ESCALATION_STAGE_UPDATE`
- `status`: `SUCCESS`
- `metadata_json`: `previous_stage`, `new_stage`, `overdue_days`

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
- POST /workflows/process-overdue
- GET /workflows/overdue
- GET /workflows/escalated
- GET /workflows/stage/{stage}
- GET /audit

## Smoke Testing

Run the workflow smoke test (backend must be running):

```bash
python backend/scripts/workflow_smoke_test.py --base-url http://localhost:8000 --cleanup
```

What it checks:

- Escalation staging across all overdue ranges
- Workflow processing endpoint stability
- Audit log creation for escalations
- Stage filtering endpoints

## Database Initialization

The SQLite database is created automatically on backend startup.

Optional seed data:

```bash
python backend/app/db/seed.py
```
