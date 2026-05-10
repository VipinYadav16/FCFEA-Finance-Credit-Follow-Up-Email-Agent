from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field
from pydantic import condecimal, conint

from app.models.enums import DeliveryStatus, EscalationStage, PaymentStatus
from app.utils.overdue import calculate_overdue_days, is_invoice_overdue


class HealthStatus(BaseModel):
    status: str
    app: str


class CreateInvoiceRequest(BaseModel):
    invoice_id: str = Field(..., min_length=1, description="External invoice identifier")
    client_name: str = Field(..., min_length=1, description="Client legal name")
    client_email: EmailStr = Field(..., description="Client billing contact email")
    amount_due: condecimal(gt=0, max_digits=12, decimal_places=2) = Field(
        ..., description="Outstanding amount due"
    )
    due_date: date = Field(..., description="Invoice due date")
    follow_up_count: conint(ge=0) = Field(0, description="Number of follow-up attempts")
    current_stage: EscalationStage = Field(
        EscalationStage.STAGE_1, description="Current escalation stage"
    )
    payment_status: PaymentStatus = Field(
        PaymentStatus.PENDING, description="Current payment status"
    )
    last_followup_date: datetime | None = Field(
        None, description="UTC timestamp of last follow-up"
    )


class UpdateInvoiceRequest(BaseModel):
    client_name: str | None = Field(None, min_length=1)
    client_email: EmailStr | None = None
    amount_due: condecimal(gt=0, max_digits=12, decimal_places=2) | None = None
    due_date: date | None = None
    follow_up_count: conint(ge=0) | None = None
    current_stage: EscalationStage | None = None
    payment_status: PaymentStatus | None = None
    last_followup_date: datetime | None = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: str
    client_name: str
    client_email: EmailStr
    amount_due: Decimal
    due_date: date
    follow_up_count: int
    current_stage: EscalationStage
    payment_status: PaymentStatus
    last_followup_date: datetime | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def overdue_days(self) -> int:
        return calculate_overdue_days(self.due_date)

    @computed_field
    @property
    def is_overdue(self) -> bool:
        return is_invoice_overdue(self.due_date)


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: str
    action_type: str
    status: str
    timestamp: datetime
    metadata_json: dict[str, Any] | None


class WorkflowInvoiceContext(BaseModel):
    invoice_id: str
    client_name: str
    client_email: EmailStr
    amount_due: Decimal
    due_date: date
    overdue_days: int
    escalation_stage: EscalationStage
    payment_status: PaymentStatus
    follow_up_count: int


class WorkflowRunSummary(BaseModel):
    started_at: datetime
    finished_at: datetime
    processed_count: int
    updated_count: int
    skipped_count: int
    error_count: int
    overdue_count: int
    escalated_count: int
    legal_escalation_count: int
    duration_seconds: float
    stage_counts: dict[str, int]
    updated_invoices: list[WorkflowInvoiceContext]


class AIEmailOutput(BaseModel):
    subject: str = Field(..., min_length=3, max_length=255)
    email_body: str = Field(..., min_length=30, max_length=5000)
    tone_used: str = Field(..., min_length=3, max_length=100)
    escalation_stage: EscalationStage


class AIValidationIssue(BaseModel):
    code: str
    message: str
    severity: str = "error"


class AIEmailGenerationResponse(BaseModel):
    invoice_id: str
    generated_at: datetime
    model_name: str
    prompt_version: str
    stage_prompt_name: str
    generation_latency_ms: int
    validation_passed: bool
    validation_issues: list[AIValidationIssue]
    tone_consistent: bool
    output_complete: bool
    output: AIEmailOutput


class AIBatchGenerateRequest(BaseModel):
    limit: int = Field(20, ge=1, le=200, description="Max overdue invoices to generate preview for")


class AIBatchGenerateResponse(BaseModel):
    generated_count: int
    failed_count: int
    items: list[AIEmailGenerationResponse]
    failures: list[dict[str, str]]


class GeneratedEmailPreviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: str
    escalation_stage: EscalationStage
    tone_used: str
    subject: str
    email_body: str
    content_summary: str
    generated_at: datetime


class DeliveryRejectRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)


class DeliveryStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invoice_id: str
    delivery_status: DeliveryStatus
    delivery_mode: str
    approved_at: datetime | None
    rejected_at: datetime | None
    sent_at: datetime | None
    rejection_reason: str | None
    last_error: str | None
    metadata_json: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class DeliveryActionResponse(BaseModel):
    invoice_id: str
    delivery_status: DeliveryStatus
    message: str
    timestamp: datetime
    metadata: dict[str, Any] | None = None


class DeliverySummaryResponse(BaseModel):
    counts: dict[str, int]
