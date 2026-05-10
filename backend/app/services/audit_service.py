import logging
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.orm import AuditLog
from app.utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)


def create_audit_log(
    db: Session,
    *,
    invoice_id: str,
    action_type: str,
    status: str,
    metadata_json: dict | None = None,
) -> AuditLog:
    audit = AuditLog(
        invoice_id=invoice_id,
        action_type=action_type,
        status=status,
        timestamp=datetime.now(timezone.utc),
        metadata_json=metadata_json,
    )
    db.add(audit)
    try:
        db.commit()
        db.refresh(audit)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to create audit log")
        raise DatabaseError("Failed to create audit log") from exc

    return audit


def list_audit_logs(db: Session, limit: int = 100) -> list[AuditLog]:
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
