from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.schemas import (
    OrchestrationRunResponse,
    OrchestrationStatusResponse,
    OrchestrationTraceResponse,
)
from app.services import orchestration_service
from app.utils.exceptions import AppError

router = APIRouter()


@router.post("/run/{invoice_id}", response_model=OrchestrationRunResponse)
def run_workflow(invoice_id: str, db: Session = Depends(get_db)) -> OrchestrationRunResponse:
    try:
        return orchestration_service.run_invoice_workflow(db, invoice_id)
    except AppError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/resume/{invoice_id}", response_model=OrchestrationRunResponse)
def resume_workflow(invoice_id: str, db: Session = Depends(get_db)) -> OrchestrationRunResponse:
    try:
        return orchestration_service.resume_workflow(db, invoice_id)
    except AppError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/trace/{invoice_id}", response_model=OrchestrationTraceResponse)
def trace_workflow(invoice_id: str) -> OrchestrationTraceResponse:
    try:
        return orchestration_service.get_workflow_trace(invoice_id)
    except AppError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/status/{invoice_id}", response_model=OrchestrationStatusResponse)
def workflow_status(invoice_id: str) -> OrchestrationStatusResponse:
    return orchestration_service.get_workflow_status(invoice_id)
