import json
import logging
from datetime import datetime, timezone

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.prompt_loader import load_stage_prompt, load_system_prompt
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.safety import build_user_prompt, validate_ai_output
from app.models.schemas import AIEmailGenerationResponse, AIEmailOutput, WorkflowInvoiceContext
from app.services import ai_preview_service, invoice_service, workflow_service
from app.utils.config import settings
from app.utils.exceptions import AIOutputValidationError, AIProviderError, InvoiceNotFoundError
from app.utils.overdue import is_invoice_overdue

logger = logging.getLogger(__name__)


def _context_for_invoice_id(db: Session, invoice_id: str) -> WorkflowInvoiceContext:
    invoice = invoice_service.get_invoice_by_invoice_id(db, invoice_id)
    return workflow_service.build_workflow_context(invoice)


def generate_followup_email(db: Session, invoice_id: str) -> AIEmailGenerationResponse:
    context = _context_for_invoice_id(db, invoice_id)
    if not is_invoice_overdue(context.due_date):
        raise AIOutputValidationError("Email generation allowed only for overdue invoices")

    system_prompt = load_system_prompt()
    stage_prompt = load_stage_prompt(context.escalation_stage)
    user_prompt = build_user_prompt(context, stage_prompt)

    provider = GeminiProvider()
    logger.info(
        "AI generation started for invoice %s at stage %s",
        context.invoice_id,
        context.escalation_stage.value,
    )
    provider_json = provider.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)

    try:
        parsed = json.loads(provider_json)
    except json.JSONDecodeError as exc:
        logger.warning("AI returned non-JSON output for invoice %s", context.invoice_id)
        raise AIOutputValidationError("AI output is not valid JSON") from exc

    try:
        output = AIEmailOutput.model_validate(parsed)
    except ValidationError as exc:
        logger.warning("AI output schema validation failed for invoice %s", context.invoice_id)
        raise AIOutputValidationError("AI output schema validation failed") from exc

    validate_ai_output(output, context)

    ai_preview_service.create_preview(
        db,
        invoice_id=context.invoice_id,
        escalation_stage=context.escalation_stage,
        output=output,
    )
    logger.info(
        "AI generation succeeded for invoice %s with tone %s",
        context.invoice_id,
        output.tone_used,
    )
    return AIEmailGenerationResponse(
        invoice_id=context.invoice_id,
        generated_at=datetime.now(timezone.utc),
        model_name=settings.gemini_model_name,
        output=output,
    )


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
