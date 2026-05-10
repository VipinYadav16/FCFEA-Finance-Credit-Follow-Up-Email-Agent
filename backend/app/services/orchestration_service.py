from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.schemas import (
    OrchestrationRunResponse,
    OrchestrationStatusResponse,
    OrchestrationTraceEvent,
    OrchestrationTraceResponse,
)
from app.services import delivery_service
from app.utils.exceptions import AppError
from app.workflows.graph.graph_builder import build_resume_graph, build_workflow_graph
from app.workflows.graph.state import OrchestrationState

logger = logging.getLogger(__name__)

_STATE_STORE: dict[str, OrchestrationState] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _base_state(invoice_id: str) -> OrchestrationState:
    return OrchestrationState(
        invoice_id=invoice_id,
        escalation_stage=None,
        workflow_status="NOT_STARTED",
        approval_status="UNKNOWN",
        delivery_status=None,
        ai_output=None,
        validation_status="UNKNOWN",
        execution_trace=[],
        error_state=None,
        current_node=None,
        started_at=_now(),
        updated_at=_now(),
        ai_result=None,
        should_send=False,
        needs_approval=False,
    )


def _status_from_state(state: OrchestrationState) -> str:
    if state.get("error_state"):
        return "FAILED"
    if state.get("approval_status") == "PENDING":
        return "PAUSED_APPROVAL"
    if state.get("delivery_status") is not None:
        return "COMPLETED"
    return "RUNNING"


def _trace_events(state: OrchestrationState) -> list[OrchestrationTraceEvent]:
    events = state.get("execution_trace", [])
    return [
        OrchestrationTraceEvent(
            node=event["node"],
            status=event["status"],
            timestamp=datetime.fromisoformat(event["timestamp"]),
            duration_ms=event["duration_ms"],
            message=event.get("message"),
            metadata=event.get("metadata"),
        )
        for event in events
    ]


def run_invoice_workflow(db: Session, invoice_id: str) -> OrchestrationRunResponse:
    state = _base_state(invoice_id)
    state["workflow_status"] = "RUNNING"
    logger.info("Orchestration run started for invoice %s", invoice_id)
    app = build_workflow_graph(db)
    try:
        result = app.invoke(state)
    except Exception as exc:  # noqa: BLE001
        state["error_state"] = str(exc)
        state["workflow_status"] = "FAILED"
        state["updated_at"] = _now()
        _STATE_STORE[invoice_id] = state
        logger.exception("Orchestration run failed for %s", invoice_id)
        raise AppError(f"Orchestration run failed: {exc}") from exc

    result["workflow_status"] = _status_from_state(result)
    result["updated_at"] = _now()
    _STATE_STORE[invoice_id] = result
    message = "Workflow paused for approval" if result["workflow_status"] == "PAUSED_APPROVAL" else "Workflow run completed"
    logger.info("Orchestration run finished for invoice %s status=%s", invoice_id, result["workflow_status"])
    return OrchestrationRunResponse(
        invoice_id=invoice_id,
        workflow_status=result["workflow_status"],
        message=message,
        trace_events=_trace_events(result),
    )


def resume_workflow(db: Session, invoice_id: str) -> OrchestrationRunResponse:
    existing = _STATE_STORE.get(invoice_id)
    if existing is None:
        raise AppError("No orchestration state found. Run workflow first.")
    existing["workflow_status"] = "RUNNING"
    existing["updated_at"] = _now()
    logger.info("Orchestration resume started for invoice %s", invoice_id)

    app = build_resume_graph(db)
    try:
        result = app.invoke(existing)
    except Exception as exc:  # noqa: BLE001
        existing["error_state"] = str(exc)
        existing["workflow_status"] = "FAILED"
        existing["updated_at"] = _now()
        _STATE_STORE[invoice_id] = existing
        logger.exception("Orchestration resume failed for %s", invoice_id)
        raise AppError(f"Orchestration resume failed: {exc}") from exc

    delivery_status = delivery_service.get_delivery_status(db, invoice_id)
    result["delivery_status"] = delivery_status.delivery_status
    result["workflow_status"] = _status_from_state(result)
    result["updated_at"] = _now()
    _STATE_STORE[invoice_id] = result
    message = "Workflow resumed and completed" if result["workflow_status"] == "COMPLETED" else "Workflow still pending approval"
    logger.info("Orchestration resume finished for invoice %s status=%s", invoice_id, result["workflow_status"])
    return OrchestrationRunResponse(
        invoice_id=invoice_id,
        workflow_status=result["workflow_status"],
        message=message,
        trace_events=_trace_events(result),
    )


def get_workflow_trace(invoice_id: str) -> OrchestrationTraceResponse:
    state = _STATE_STORE.get(invoice_id)
    if state is None:
        raise AppError("No orchestration state found for invoice")
    return OrchestrationTraceResponse(
        invoice_id=invoice_id,
        workflow_status=state.get("workflow_status", "NOT_STARTED"),
        trace_events=_trace_events(state),
    )


def get_workflow_status(invoice_id: str) -> OrchestrationStatusResponse:
    state = _STATE_STORE.get(invoice_id)
    if state is None:
        return OrchestrationStatusResponse(
            invoice_id=invoice_id,
            workflow_status="NOT_STARTED",
            approval_status="UNKNOWN",
            delivery_status=None,
            current_node=None,
            error_state=None,
            started_at=None,
            updated_at=None,
        )
    return OrchestrationStatusResponse(
        invoice_id=invoice_id,
        workflow_status=state.get("workflow_status", "NOT_STARTED"),
        approval_status=state.get("approval_status", "UNKNOWN"),
        delivery_status=state.get("delivery_status"),
        current_node=state.get("current_node"),
        error_state=state.get("error_state"),
        started_at=state.get("started_at"),
        updated_at=state.get("updated_at"),
    )
