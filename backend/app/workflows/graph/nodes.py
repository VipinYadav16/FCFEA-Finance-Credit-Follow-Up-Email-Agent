from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Callable

from sqlalchemy.orm import Session

from app.models.enums import DeliveryStatus
from app.services import (
    ai_generation_service,
    ai_preview_service,
    audit_service,
    delivery_service,
    invoice_service,
    workflow_service,
)
from app.utils.exceptions import AppError
from app.workflows.graph.state import OrchestrationState, TraceEvent


def _append_trace(
    state: OrchestrationState,
    *,
    node: str,
    status: str,
    started: float,
    message: str | None = None,
    metadata: dict | None = None,
) -> None:
    event: TraceEvent = {
        "node": node,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": int((perf_counter() - started) * 1000),
        "message": message,
        "metadata": metadata,
    }
    state.setdefault("execution_trace", []).append(event)
    state["updated_at"] = datetime.now(timezone.utc)
    state["current_node"] = node


def fetch_invoice_node(db: Session) -> Callable[[OrchestrationState], OrchestrationState]:
    def node(state: OrchestrationState) -> OrchestrationState:
        started = perf_counter()
        invoice_id = state["invoice_id"]
        invoice = invoice_service.get_invoice_by_invoice_id(db, invoice_id)
        context = workflow_service.build_workflow_context(invoice)
        state["escalation_stage"] = context.escalation_stage
        _append_trace(
            state,
            node="fetch_invoice",
            status="SUCCESS",
            started=started,
            metadata={"escalation_stage": context.escalation_stage.value},
        )
        return state

    return node


def process_workflow_node(db: Session) -> Callable[[OrchestrationState], OrchestrationState]:
    def node(state: OrchestrationState) -> OrchestrationState:
        started = perf_counter()
        summary = workflow_service.process_overdue_invoices(db)
        _append_trace(
            state,
            node="workflow_processing",
            status="SUCCESS",
            started=started,
            metadata={
                "processed_count": summary.processed_count,
                "updated_count": summary.updated_count,
            },
        )
        return state

    return node


def ai_generation_node(db: Session) -> Callable[[OrchestrationState], OrchestrationState]:
    def node(state: OrchestrationState) -> OrchestrationState:
        started = perf_counter()
        result = ai_generation_service.generate_followup_email(db, state["invoice_id"])
        state["ai_result"] = result
        state["ai_output"] = result.output.model_dump()
        state["validation_status"] = "PASSED" if result.validation_passed else "FAILED"
        _append_trace(
            state,
            node="ai_generation",
            status="SUCCESS",
            started=started,
            metadata={
                "validation_passed": result.validation_passed,
                "tone_consistent": result.tone_consistent,
            },
        )
        return state

    return node


def ai_validation_node() -> Callable[[OrchestrationState], OrchestrationState]:
    def node(state: OrchestrationState) -> OrchestrationState:
        started = perf_counter()
        ai_result = state.get("ai_result")
        if ai_result is None or not ai_result.validation_passed:
            state["validation_status"] = "FAILED"
            _append_trace(
                state,
                node="ai_validation",
                status="FAILED",
                started=started,
                message="AI output validation failed",
            )
            raise AppError("AI output validation failed in orchestration")
        state["validation_status"] = "PASSED"
        _append_trace(state, node="ai_validation", status="SUCCESS", started=started)
        return state

    return node


def preview_creation_node(db: Session) -> Callable[[OrchestrationState], OrchestrationState]:
    def node(state: OrchestrationState) -> OrchestrationState:
        started = perf_counter()
        preview = ai_preview_service.get_latest_preview_by_invoice_id(db, state["invoice_id"])
        if preview is None:
            _append_trace(
                state,
                node="preview_creation",
                status="FAILED",
                started=started,
                message="Preview not found",
            )
            raise AppError("Generated preview missing")
        _append_trace(state, node="preview_creation", status="SUCCESS", started=started)
        return state

    return node


def approval_wait_node(db: Session) -> Callable[[OrchestrationState], OrchestrationState]:
    def node(state: OrchestrationState) -> OrchestrationState:
        started = perf_counter()
        status = delivery_service.get_delivery_status(db, state["invoice_id"])
        state["delivery_status"] = status.delivery_status
        if status.delivery_status == DeliveryStatus.APPROVED:
            state["approval_status"] = "APPROVED"
            state["should_send"] = True
            _append_trace(state, node="approval_wait", status="RESUME_APPROVED", started=started)
            return state
        if status.delivery_status == DeliveryStatus.REJECTED:
            state["approval_status"] = "REJECTED"
            state["should_send"] = False
            _append_trace(state, node="approval_wait", status="STOP_REJECTED", started=started)
            return state
        state["approval_status"] = "PENDING"
        state["needs_approval"] = True
        state["should_send"] = False
        _append_trace(state, node="approval_wait", status="PAUSED_PENDING_APPROVAL", started=started)
        return state

    return node


def dry_run_delivery_node(db: Session) -> Callable[[OrchestrationState], OrchestrationState]:
    def node(state: OrchestrationState) -> OrchestrationState:
        started = perf_counter()
        if not state.get("should_send", False):
            _append_trace(
                state,
                node="dry_run_delivery",
                status="SKIPPED",
                started=started,
                message="Delivery skipped due to approval state",
            )
            return state
        delivery = delivery_service.dry_run_send(db, state["invoice_id"])
        state["delivery_status"] = delivery.delivery_status
        _append_trace(
            state,
            node="dry_run_delivery",
            status="SUCCESS",
            started=started,
            metadata=delivery.metadata,
        )
        return state

    return node


def audit_complete_node(db: Session) -> Callable[[OrchestrationState], OrchestrationState]:
    def node(state: OrchestrationState) -> OrchestrationState:
        started = perf_counter()
        audit_service.create_audit_log(
            db,
            invoice_id=state["invoice_id"],
            action_type="ORCHESTRATION_RUN",
            status="SUCCESS" if state.get("should_send", False) else state.get("approval_status", "PENDING"),
            metadata_json={
                "workflow_status": state.get("workflow_status"),
                "current_node": state.get("current_node"),
            },
        )
        _append_trace(state, node="audit_complete", status="SUCCESS", started=started)
        return state

    return node
