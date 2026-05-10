from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.schemas import CreateInvoiceRequest, InvoiceResponse, UpdateInvoiceRequest
from app.services import invoice_service
from app.utils.exceptions import DatabaseError, DuplicateInvoiceError, InvoiceNotFoundError

router = APIRouter()


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(request: CreateInvoiceRequest, db: Session = Depends(get_db)) -> InvoiceResponse:
    try:
        invoice = invoice_service.create_invoice(db, request)
    except DuplicateInvoiceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except DatabaseError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return InvoiceResponse.model_validate(invoice)


@router.get("/", response_model=list[InvoiceResponse])
def list_invoices(db: Session = Depends(get_db)) -> list[InvoiceResponse]:
    invoices = invoice_service.get_all_invoices(db)
    return [InvoiceResponse.model_validate(invoice) for invoice in invoices]


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)) -> InvoiceResponse:
    try:
        invoice = invoice_service.get_invoice_by_invoice_id(db, invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return InvoiceResponse.model_validate(invoice)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: str, request: UpdateInvoiceRequest, db: Session = Depends(get_db)
) -> InvoiceResponse:
    try:
        invoice = invoice_service.update_invoice(db, invoice_id, request)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DatabaseError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return InvoiceResponse.model_validate(invoice)


@router.delete("/{invoice_id}", response_model=InvoiceResponse)
def delete_invoice(invoice_id: str, db: Session = Depends(get_db)) -> InvoiceResponse:
    try:
        invoice = invoice_service.delete_invoice(db, invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DatabaseError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return InvoiceResponse.model_validate(invoice)
