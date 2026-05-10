# Demo Rehearsal Checklist

## Startup Sequence

- [ ] Confirm `.env` exists and `BACKEND_URL` is correct
- [ ] Start backend: `python -m uvicorn app.main:app --app-dir backend --reload`
- [ ] Start frontend: `python -m streamlit run frontend/streamlit_app.py`
- [ ] Open dashboard and confirm API connectivity

## Demo Flow Order

- [ ] Show invoice table with overdue mix
- [ ] Trigger deterministic workflow processing
- [ ] Explain escalation stage outcomes (Stage 1-4 + Legal)
- [ ] Generate AI email preview for one overdue invoice
- [ ] Show AI validation/safety acceptance
- [ ] Approve generated message from approval queue
- [ ] Execute dry-run send and show status transition
- [ ] Run orchestration flow and show pause/resume behavior
- [ ] Open orchestration trace and explain timeline
- [ ] Open audit logs and show traceability evidence

## Important Talking Points

- [ ] Deterministic workflow engine owns business logic
- [ ] AI is constrained to communication generation only
- [ ] Validation layer blocks unsafe or fabricated language
- [ ] Human approval is mandatory before delivery
- [ ] Dry-run mode enforces safe operational testing
- [ ] LangGraph coordinates services without replacing domain logic

## Fallback Demo Strategy

- [ ] If Gemini/API key unavailable: use existing sample AI outputs
- [ ] If orchestration execution fails live: show stored sample orchestration trace
- [ ] If backend startup issue occurs: present architecture + API docs + sample outputs path
- [ ] If UI issue occurs: demonstrate endpoints via API docs/curl and resume UI when stable

## Backup Screenshots

- [ ] Dashboard overview screenshot
- [ ] Escalation/workflow snapshot
- [ ] AI preview + validation snapshot
- [ ] Approval queue snapshot
- [ ] Dry-run delivery status snapshot
- [ ] Orchestration trace snapshot
- [ ] Audit log snapshot

Recommended storage: `docs/assets/`
