from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import EscalationStage
from app.models.schemas import WorkflowInvoiceContext, WorkflowRunSummary
from app.services import workflow_service
from app.utils.exceptions import WorkflowProcessingError
from app.utils.workflow import parse_stage

router = APIRouter()


@router.post("/process-overdue", response_model=WorkflowRunSummary)
def process_overdue(db: Session = Depends(get_db)) -> WorkflowRunSummary:
    try:
        return workflow_service.process_overdue_invoices(db)
    except WorkflowProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/overdue", response_model=list[WorkflowInvoiceContext])
def list_overdue(db: Session = Depends(get_db)) -> list[WorkflowInvoiceContext]:
    return workflow_service.get_overdue_invoices(db)


@router.get("/escalated", response_model=list[WorkflowInvoiceContext])
def list_escalated(db: Session = Depends(get_db)) -> list[WorkflowInvoiceContext]:
    return workflow_service.get_escalated_invoices(db)


@router.get("/stage/{stage}", response_model=list[WorkflowInvoiceContext])
def list_by_stage(stage: str, db: Session = Depends(get_db)) -> list[WorkflowInvoiceContext]:
    stage_enum: EscalationStage | None = parse_stage(stage)
    if stage_enum is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage '{stage}'",
        )
    return workflow_service.get_invoices_by_stage(db, stage_enum)
