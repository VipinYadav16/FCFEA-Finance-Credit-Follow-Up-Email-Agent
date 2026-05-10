from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.schemas import AuditLogResponse
from app.services import audit_service

router = APIRouter()


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(limit: int = 100, db: Session = Depends(get_db)) -> list[AuditLogResponse]:
    logs = audit_service.list_audit_logs(db, limit=limit)
    return [AuditLogResponse.model_validate(log) for log in logs]
