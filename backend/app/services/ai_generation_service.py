import json
import logging
from datetime import datetime, timezone
from time import perf_counter

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.evaluation import evaluate_output_completeness, evaluate_tone_consistency
from app.ai.prompt_loader import load_stage_prompt, load_system_prompt
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.safety import build_user_prompt
from app.ai.sanitization import sanitize_generated_output_text
from app.ai.validation import ValidationIssue, validate_ai_output
from app.models.schemas import (
    AIEmailGenerationResponse,
    AIEmailOutput,
    AIValidationIssue,
    WorkflowInvoiceContext,
)
from app.services import ai_preview_service, audit_service, invoice_service, workflow_service
from app.utils.config import settings
from app.utils.exceptions import AIOutputValidationError, AIProviderError, InvoiceNotFoundError
from app.utils.overdue import is_invoice_overdue

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v1.1"


def _context_for_invoice_id(db: Session, invoice_id: str) -> WorkflowInvoiceContext:
    invoice = invoice_service.get_invoice_by_invoice_id(db, invoice_id)
    return workflow_service.build_workflow_context(invoice)


def _to_validation_issues(issues: list[ValidationIssue]) -> list[AIValidationIssue]:
    return [AIValidationIssue(code=i.code, message=i.message, severity=i.severity) for i in issues]


def _sanitize_output(output: AIEmailOutput) -> AIEmailOutput:
    return AIEmailOutput(
        subject=sanitize_generated_output_text(output.subject, max_len=255),
        email_body=sanitize_generated_output_text(output.email_body, max_len=5000),
        tone_used=sanitize_generated_output_text(output.tone_used, max_len=100),
        escalation_stage=output.escalation_stage,
    )


def _build_response(
    *,
    context: WorkflowInvoiceContext,
    output: AIEmailOutput,
    stage_prompt_name: str,
    started_at: float,
    validation_issues: list[AIValidationIssue],
) -> AIEmailGenerationResponse:
    latency_ms = int((perf_counter() - started_at) * 1000)
    tone_consistent = evaluate_tone_consistency(output)
    output_complete = evaluate_output_completeness(output)
    validation_passed = len(validation_issues) == 0
    return AIEmailGenerationResponse(
        invoice_id=context.invoice_id,
        generated_at=datetime.now(timezone.utc),
        model_name=settings.openai_model_name,
        prompt_version=PROMPT_VERSION,
        stage_prompt_name=stage_prompt_name,
        generation_latency_ms=latency_ms,
        validation_passed=validation_passed,
        validation_issues=validation_issues,
        tone_consistent=tone_consistent,
        output_complete=output_complete,
        output=output,
    )


def generate_followup_email(db: Session, invoice_id: str) -> AIEmailGenerationResponse:
    started = perf_counter()
    context = _context_for_invoice_id(db, invoice_id)
    if not is_invoice_overdue(context.due_date):
        raise AIOutputValidationError("Email generation allowed only for overdue invoices")

    stage_prompt_name = f"{context.escalation_stage.value.lower()}.txt"
    system_prompt = load_system_prompt()
    stage_prompt = load_stage_prompt(context.escalation_stage)
    user_prompt = build_user_prompt(context, stage_prompt)

    provider = OpenAIProvider()
    logger.info(
        "AI generation started for invoice=%s stage=%s prompt_version=%s",
        context.invoice_id,
        context.escalation_stage.value,
        PROMPT_VERSION,
    )
    audit_service.create_audit_log(
        db,
        invoice_id=context.invoice_id,
        action_type="AI_GENERATION_ATTEMPT",
        status="STARTED",
        metadata_json={
            "model_name": settings.openai_model_name,
            "prompt_version": PROMPT_VERSION,
            "stage_prompt_name": stage_prompt_name,
        },
    )
    provider_json = provider.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)

    try:
        parsed = json.loads(provider_json)
    except json.JSONDecodeError as exc:
        logger.warning("AI returned non-JSON output for invoice %s", context.invoice_id)
        audit_service.create_audit_log(
            db,
            invoice_id=context.invoice_id,
            action_type="AI_GENERATION_ATTEMPT",
            status="REJECTED_NON_JSON",
            metadata_json={"prompt_version": PROMPT_VERSION},
        )
        raise AIOutputValidationError("AI output is not valid JSON") from exc

    try:
        output = AIEmailOutput.model_validate(parsed)
    except ValidationError as exc:
        logger.warning("AI output schema validation failed for invoice %s", context.invoice_id)
        audit_service.create_audit_log(
            db,
            invoice_id=context.invoice_id,
            action_type="AI_GENERATION_ATTEMPT",
            status="REJECTED_SCHEMA",
            metadata_json={"prompt_version": PROMPT_VERSION},
        )
        raise AIOutputValidationError("AI output schema validation failed") from exc

    sanitized = _sanitize_output(output)
    validation_result = validate_ai_output(sanitized, context)
    issues = _to_validation_issues(validation_result.issues)
    if not validation_result.is_valid:
        issue_payload = [issue.model_dump() for issue in issues]
        logger.warning("AI output rejected for invoice %s issues=%s", context.invoice_id, issue_payload)
        audit_service.create_audit_log(
            db,
            invoice_id=context.invoice_id,
            action_type="AI_GENERATION_ATTEMPT",
            status="REJECTED_VALIDATION",
            metadata_json={
                "issues": issue_payload,
                "prompt_version": PROMPT_VERSION,
                "stage_prompt_name": stage_prompt_name,
            },
        )
        raise AIOutputValidationError("AI output rejected by validation rules")

    ai_preview_service.create_preview(
        db,
        invoice_id=context.invoice_id,
        escalation_stage=context.escalation_stage,
        output=sanitized,
    )
    response = _build_response(
        context=context,
        output=sanitized,
        stage_prompt_name=stage_prompt_name,
        started_at=started,
        validation_issues=issues,
    )
    audit_service.create_audit_log(
        db,
        invoice_id=context.invoice_id,
        action_type="AI_GENERATION_ATTEMPT",
        status="SUCCESS",
        metadata_json={
            "model_name": response.model_name,
            "prompt_version": response.prompt_version,
            "stage_prompt_name": response.stage_prompt_name,
            "latency_ms": response.generation_latency_ms,
            "tone_consistent": response.tone_consistent,
            "output_complete": response.output_complete,
        },
    )
    logger.info(
        "AI generation succeeded for invoice=%s stage=%s latency_ms=%s",
        context.invoice_id,
        context.escalation_stage.value,
        response.generation_latency_ms,
    )
    return response


def generate_overdue_batch(db: Session, limit: int) -> tuple[list[AIEmailGenerationResponse], list[dict[str, str]]]:
    overdue_contexts = workflow_service.get_overdue_invoices(db)[:limit]
    items: list[AIEmailGenerationResponse] = []
    failures: list[dict[str, str]] = []
    for context in overdue_contexts:
        try:
            items.append(generate_followup_email(db, context.invoice_id))
        except (InvoiceNotFoundError, AIProviderError, AIOutputValidationError) as exc:
            logger.warning("Batch generation failed for %s: %s", context.invoice_id, exc)
            failures.append({"invoice_id": context.invoice_id, "error": str(exc)})
    return items, failures
