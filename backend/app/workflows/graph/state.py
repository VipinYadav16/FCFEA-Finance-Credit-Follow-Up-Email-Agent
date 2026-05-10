from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TypedDict

from app.models.enums import DeliveryStatus, EscalationStage
from app.models.schemas import AIEmailGenerationResponse


class TraceEvent(TypedDict):
    node: str
    status: str
    timestamp: str
    duration_ms: int
    message: str | None
    metadata: dict[str, Any] | None


class OrchestrationState(TypedDict, total=False):
    invoice_id: str
    escalation_stage: EscalationStage | None
    workflow_status: Literal["NOT_STARTED", "RUNNING", "PAUSED_APPROVAL", "FAILED", "COMPLETED"]
    approval_status: Literal["UNKNOWN", "PENDING", "APPROVED", "REJECTED"]
    delivery_status: DeliveryStatus | None
    ai_output: dict[str, Any] | None
    validation_status: Literal["UNKNOWN", "PASSED", "FAILED"]
    execution_trace: list[TraceEvent]
    error_state: str | None
    current_node: str | None
    started_at: datetime | None
    updated_at: datetime | None
    ai_result: AIEmailGenerationResponse | None
    should_send: bool
    needs_approval: bool
