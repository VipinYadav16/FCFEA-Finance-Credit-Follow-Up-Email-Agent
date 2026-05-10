import re
from decimal import Decimal

from app.models.schemas import AIEmailOutput, WorkflowInvoiceContext
from app.utils.exceptions import AIOutputValidationError

_INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"system\s+prompt",
    r"developer\s+message",
    r"act\s+as",
]
_FORBIDDEN_OUTPUT_PATTERNS = [
    r"\blegal action\b",
    r"\blawsuit\b",
    r"\bpenalty\b",
    r"\bcriminal\b",
    r"\bharass\b",
]


def sanitize_prompt_field(value: str, max_len: int = 200) -> str:
    cleaned = value.replace("\n", " ").replace("\r", " ").strip()
    scrubbed = cleaned
    for pattern in _INJECTION_PATTERNS:
        scrubbed = re.sub(pattern, "[redacted]", scrubbed, flags=re.IGNORECASE)
    if len(scrubbed) > max_len:
        return scrubbed[:max_len]
    return scrubbed


def build_user_prompt(context: WorkflowInvoiceContext, stage_prompt: str) -> str:
    client_name = sanitize_prompt_field(context.client_name, max_len=120)
    invoice_id = sanitize_prompt_field(context.invoice_id, max_len=80)
    return (
        "Use the policy and deterministic context below to generate a follow-up email preview.\n\n"
        f"Stage policy:\n{stage_prompt}\n\n"
        "Deterministic context:\n"
        f"- invoice_id: {invoice_id}\n"
        f"- client_name: {client_name}\n"
        f"- client_email: {context.client_email}\n"
        f"- amount_due: {Decimal(context.amount_due):.2f}\n"
        f"- due_date: {context.due_date.isoformat()}\n"
        f"- overdue_days: {context.overdue_days}\n"
        f"- escalation_stage: {context.escalation_stage.value}\n"
        f"- payment_status: {context.payment_status.value}\n"
        f"- follow_up_count: {context.follow_up_count}\n\n"
        "Output JSON only with keys: subject, email_body, tone_used, escalation_stage."
    )


def validate_ai_output(output: AIEmailOutput, context: WorkflowInvoiceContext) -> None:
    if output.escalation_stage != context.escalation_stage:
        raise AIOutputValidationError("Escalation stage mismatch in AI output")
    if context.invoice_id not in output.email_body:
        raise AIOutputValidationError("Generated email body must include invoice_id")
    amount_token = f"{Decimal(context.amount_due):.2f}"
    if amount_token not in output.email_body:
        raise AIOutputValidationError("Generated email body must include deterministic amount_due")

    merged_text = f"{output.subject}\n{output.email_body}"
    for pattern in _FORBIDDEN_OUTPUT_PATTERNS:
        if re.search(pattern, merged_text, flags=re.IGNORECASE):
            raise AIOutputValidationError("Unsafe language detected in generated output")
