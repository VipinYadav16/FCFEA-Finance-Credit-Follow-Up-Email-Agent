from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.schemas import (
    DeliveryActionResponse,
    DeliveryRejectRequest,
    DeliveryStatusResponse,
    DeliverySummaryResponse,
)
from app.services import delivery_service
from app.utils.exceptions import DeliveryStateError, InvoiceNotFoundError

router = APIRouter()


@router.post("/approve/{invoice_id}", response_model=DeliveryActionResponse)
def approve(invoice_id: str, db: Session = Depends(get_db)) -> DeliveryActionResponse:
    try:
        return delivery_service.approve_email(db, invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DeliveryStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/reject/{invoice_id}", response_model=DeliveryActionResponse)
def reject(
    invoice_id: str, request: DeliveryRejectRequest, db: Session = Depends(get_db)
) -> DeliveryActionResponse:
    try:
        return delivery_service.reject_email(db, invoice_id, request.reason)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DeliveryStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/dry-run-send/{invoice_id}", response_model=DeliveryActionResponse)
def dry_run_send(invoice_id: str, db: Session = Depends(get_db)) -> DeliveryActionResponse:
    try:
        return delivery_service.dry_run_send(db, invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DeliveryStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/regenerate/{invoice_id}", response_model=DeliveryActionResponse)
def regenerate(invoice_id: str, db: Session = Depends(get_db)) -> DeliveryActionResponse:
    try:
        return delivery_service.regenerate_email(db, invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DeliveryStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/status/{invoice_id}", response_model=DeliveryStatusResponse)
def status_by_invoice(invoice_id: str, db: Session = Depends(get_db)) -> DeliveryStatusResponse:
    try:
        return delivery_service.get_delivery_status(db, invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/pending-approvals", response_model=list[DeliveryStatusResponse])
def pending_approvals(db: Session = Depends(get_db)) -> list[DeliveryStatusResponse]:
    return delivery_service.list_pending_approvals(db)


@router.get("/summary", response_model=DeliverySummaryResponse)
def summary(db: Session = Depends(get_db)) -> DeliverySummaryResponse:
    return DeliverySummaryResponse(counts=delivery_service.get_delivery_summary(db))
