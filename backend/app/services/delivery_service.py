import logging
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.delivery.providers.dry_run_provider import DryRunDeliveryProvider
from app.models.enums import DeliveryStatus
from app.models.orm import DeliveryRecord
from app.models.schemas import (
    DeliveryActionResponse,
    DeliveryStatusResponse,
    GeneratedEmailPreviewResponse,
)
from app.services import ai_generation_service, ai_preview_service, audit_service, invoice_service
from app.utils.exceptions import (
    AIOutputValidationError,
    AIProviderError,
    DatabaseError,
    DeliveryStateError,
    InvoiceNotFoundError,
    PromptLoadError,
)

logger = logging.getLogger(__name__)


def _persist(db: Session, record: DeliveryRecord) -> DeliveryRecord:
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Delivery persistence failed for invoice %s", record.invoice_id)
        raise DatabaseError("Failed to persist delivery state") from exc


def _latest_preview_or_raise(db: Session, invoice_id: str) -> GeneratedEmailPreviewResponse:
    preview = ai_preview_service.get_latest_preview_by_invoice_id(db, invoice_id)
    if preview is None:
        raise DeliveryStateError(f"No generated preview exists for invoice '{invoice_id}'")
    return GeneratedEmailPreviewResponse.model_validate(preview)


def _get_or_create_record(db: Session, invoice_id: str) -> DeliveryRecord:
    invoice_service.get_invoice_by_invoice_id(db, invoice_id)
    record = db.query(DeliveryRecord).filter(DeliveryRecord.invoice_id == invoice_id).first()
    if record:
        return record
    created = DeliveryRecord(
        invoice_id=invoice_id,
        delivery_status=DeliveryStatus.PENDING_APPROVAL,
        delivery_mode="DRY_RUN",
    )
    return _persist(db, created)


def get_delivery_status(db: Session, invoice_id: str) -> DeliveryStatusResponse:
    record = _get_or_create_record(db, invoice_id)
    return DeliveryStatusResponse.model_validate(record)


def list_pending_approvals(db: Session) -> list[DeliveryStatusResponse]:
    records = (
        db.query(DeliveryRecord)
        .filter(DeliveryRecord.delivery_status == DeliveryStatus.PENDING_APPROVAL)
        .order_by(DeliveryRecord.updated_at.asc())
        .all()
    )
    return [DeliveryStatusResponse.model_validate(record) for record in records]


def get_delivery_summary(db: Session) -> dict[str, int]:
    counts = {status.value: 0 for status in DeliveryStatus}
    rows = db.query(DeliveryRecord).all()
    for row in rows:
        counts[row.delivery_status.value] += 1
    return counts


def approve_email(db: Session, invoice_id: str) -> DeliveryActionResponse:
    _latest_preview_or_raise(db, invoice_id)
    record = _get_or_create_record(db, invoice_id)
    if record.delivery_status in {DeliveryStatus.DRY_RUN_SENT, DeliveryStatus.SENT}:
        raise DeliveryStateError("Email already sent; cannot approve again")
    if record.delivery_status == DeliveryStatus.REJECTED:
        raise DeliveryStateError("Email is rejected; regenerate before approval")
    record.delivery_status = DeliveryStatus.APPROVED
    record.approved_at = datetime.now(timezone.utc)
    record.rejected_at = None
    record.rejection_reason = None
    _persist(db, record)
    audit_service.create_audit_log(
        db,
        invoice_id=invoice_id,
        action_type="DELIVERY_APPROVAL",
        status="APPROVED",
        metadata_json={"delivery_mode": record.delivery_mode},
    )
    return DeliveryActionResponse(
        invoice_id=invoice_id,
        delivery_status=record.delivery_status,
        message="Email approved for delivery",
        timestamp=datetime.now(timezone.utc),
        metadata={"delivery_mode": record.delivery_mode},
    )


def reject_email(db: Session, invoice_id: str, reason: str) -> DeliveryActionResponse:
    _latest_preview_or_raise(db, invoice_id)
    record = _get_or_create_record(db, invoice_id)
    if record.delivery_status in {DeliveryStatus.DRY_RUN_SENT, DeliveryStatus.SENT}:
        raise DeliveryStateError("Email already sent; rejection not allowed")
    record.delivery_status = DeliveryStatus.REJECTED
    record.rejected_at = datetime.now(timezone.utc)
    record.rejection_reason = reason
    _persist(db, record)
    audit_service.create_audit_log(
        db,
        invoice_id=invoice_id,
        action_type="DELIVERY_REJECTION",
        status="REJECTED",
        metadata_json={"reason": reason},
    )
    return DeliveryActionResponse(
        invoice_id=invoice_id,
        delivery_status=record.delivery_status,
        message="Email rejected",
        timestamp=datetime.now(timezone.utc),
        metadata={"reason": reason},
    )


def dry_run_send(db: Session, invoice_id: str) -> DeliveryActionResponse:
    preview = _latest_preview_or_raise(db, invoice_id)
    record = _get_or_create_record(db, invoice_id)
    if record.delivery_status == DeliveryStatus.DRY_RUN_SENT:
        raise DeliveryStateError("Email already dry-run sent")
    if record.delivery_status != DeliveryStatus.APPROVED:
        raise DeliveryStateError("Only approved emails can be dry-run sent")

    provider = DryRunDeliveryProvider()
    try:
        metadata = provider.send(invoice_id, preview)
    except Exception as exc:  # noqa: BLE001
        record.delivery_status = DeliveryStatus.FAILED
        record.last_error = str(exc)
        _persist(db, record)
        audit_service.create_audit_log(
            db,
            invoice_id=invoice_id,
            action_type="DELIVERY_DRY_RUN",
            status="FAILED",
            metadata_json={"error": str(exc)},
        )
        raise DeliveryStateError("Dry-run delivery failed") from exc

    record.delivery_status = DeliveryStatus.DRY_RUN_SENT
    record.sent_at = datetime.now(timezone.utc)
    record.metadata_json = metadata
    record.last_error = None
    _persist(db, record)
    audit_service.create_audit_log(
        db,
        invoice_id=invoice_id,
        action_type="DELIVERY_DRY_RUN",
        status="SUCCESS",
        metadata_json=metadata,
    )
    return DeliveryActionResponse(
        invoice_id=invoice_id,
        delivery_status=record.delivery_status,
        message="Dry-run delivery executed",
        timestamp=datetime.now(timezone.utc),
        metadata=metadata,
    )


def regenerate_email(db: Session, invoice_id: str) -> DeliveryActionResponse:
    try:
        ai_generation_service.generate_followup_email(db, invoice_id)
    except (InvoiceNotFoundError, PromptLoadError, AIProviderError, AIOutputValidationError) as exc:
        raise DeliveryStateError(f"Regeneration failed: {exc}") from exc

    record = _get_or_create_record(db, invoice_id)
    record.delivery_status = DeliveryStatus.PENDING_APPROVAL
    record.approved_at = None
    record.rejected_at = None
    record.rejection_reason = None
    record.sent_at = None
    record.last_error = None
    _persist(db, record)
    audit_service.create_audit_log(
        db,
        invoice_id=invoice_id,
        action_type="DELIVERY_REGENERATE",
        status="SUCCESS",
        metadata_json={"delivery_mode": record.delivery_mode},
    )
    return DeliveryActionResponse(
        invoice_id=invoice_id,
        delivery_status=record.delivery_status,
        message="Email regenerated and moved to pending approval",
        timestamp=datetime.now(timezone.utc),
    )
