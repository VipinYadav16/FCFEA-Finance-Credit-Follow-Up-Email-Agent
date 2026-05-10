# Finance Credit Follow-Up Email Agent

Workflow-first architecture for enterprise finance follow-up with deterministic workflow logic and controlled AI communication.

## Current Architecture

- API layer: FastAPI routes under `backend/app/api`
- Service layer: domain services under `backend/app/services`
- Workflow layer: deterministic escalation engine under `backend/app/workflows`
- AI communication layer: provider abstraction, prompt files, and validation under `backend/app/ai`
- Data layer: SQLAlchemy ORM and SQLite under `backend/app/models` and `backend/app/db`
- UI layer: Streamlit API-driven dashboard under `frontend/`

## Deterministic Workflow Scope (Completed)

- Overdue invoice processing and escalation stage assignment
- Stage transition audit logging
- Workflow summaries and stage-based filters
- Smoke script for workflow stabilization

## AI Communication Layer Scope (Step 4)

- Gemini integration via provider abstraction (`BaseAIProvider`, `GeminiProvider`)
- Externalized prompt architecture:
  - `system_prompt.txt`
  - `stage_1.txt`
  - `stage_2.txt`
  - `stage_3.txt`
  - `stage_4.txt`
  - `legal_escalation.txt`
- Structured output schema validation (`AIEmailOutput`)
- Prompt injection mitigation through field sanitization
- AI output safety checks (stage consistency, deterministic field presence, unsafe-language screening)
- Generated preview persistence (`generated_email_previews` table)

## AI Hardening Scope (Step 4.5)

- Modular AI validation layer (`backend/app/ai/validation.py`)
  - required fields
  - formatting checks
  - forbidden phrase checks
  - unsafe tone checks
  - hallucination checks against deterministic context
- Output sanitization and normalization (`backend/app/ai/sanitization.py`)
- Evaluation helpers for consistency/completeness (`backend/app/ai/evaluation.py`)
- Expanded observability:
  - prompt version
  - stage prompt name
  - generation latency
  - validation status/issues
  - tone/completeness indicators
- Centralized AI attempt audit logging through `/audit` (`AI_GENERATION_ATTEMPT`)

## AI Safety Boundaries

- AI cannot control escalation, overdue logic, or workflow state decisions.
- AI output is restricted to communication rendering.
- Prompt policy prohibits fabricated penalties, legal threats, harassment, emotional manipulation, and invented invoice facts.
- Deterministic context is injected as trusted business truth for generation.
- AI output is rejected when validation rules fail.

## API Endpoints

### Core

- `POST /invoices`
- `GET /invoices`
- `GET /invoices/{invoice_id}`
- `PUT /invoices/{invoice_id}`
- `DELETE /invoices/{invoice_id}`
- `POST /workflows/process-overdue`
- `GET /workflows/overdue`
- `GET /workflows/escalated`
- `GET /workflows/stage/{stage}`
- `GET /audit`

### AI Preview

- `POST /ai/generate/{invoice_id}`
- `POST /ai/generate-overdue-batch`
- `GET /ai/generated-preview/{invoice_id}`

## Setup

1. Create virtual environment:

```bash
python -m venv venv
```

2. Activate (PowerShell):

```bash
venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment:

```bash
copy .env.example .env
```

Set `GEMINI_API_KEY` in `.env` before calling AI endpoints.

## Run Backend

```bash
python -m uvicorn app.main:app --app-dir backend --reload
```

Health endpoint: `http://localhost:8000/health`

## Run Frontend

```bash
python -m streamlit run frontend/streamlit_app.py
```

## Smoke / Test Commands

Workflow smoke test:

```bash
python backend/scripts/workflow_smoke_test.py --base-url http://localhost:8000 --cleanup
```

Unit tests:

```bash
python -m pytest -q
```
