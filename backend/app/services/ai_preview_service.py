import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.enums import EscalationStage
from app.models.orm import GeneratedEmailPreview
from app.models.schemas import AIEmailOutput
from app.utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)


def create_preview(
    db: Session,
    *,
    invoice_id: str,
    escalation_stage: EscalationStage,
    output: AIEmailOutput,
) -> GeneratedEmailPreview:
    summary = output.email_body.replace("\n", " ").strip()[:300]
    preview = GeneratedEmailPreview(
        invoice_id=invoice_id,
        escalation_stage=escalation_stage,
        tone_used=output.tone_used,
        subject=output.subject,
        email_body=output.email_body,
        content_summary=summary,
    )
    db.add(preview)
    try:
        db.commit()
        db.refresh(preview)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to persist generated preview for invoice %s", invoice_id)
        raise DatabaseError("Failed to persist generated preview") from exc
    return preview


def get_latest_preview_by_invoice_id(db: Session, invoice_id: str) -> GeneratedEmailPreview | None:
    return (
        db.query(GeneratedEmailPreview)
        .filter(GeneratedEmailPreview.invoice_id == invoice_id)
        .order_by(GeneratedEmailPreview.generated_at.desc())
        .first()
    )
