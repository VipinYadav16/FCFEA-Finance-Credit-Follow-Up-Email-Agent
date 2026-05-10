import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.orm import Invoice
from app.models.schemas import CreateInvoiceRequest, UpdateInvoiceRequest
from app.utils.exceptions import DatabaseError, DuplicateInvoiceError, InvoiceNotFoundError

logger = logging.getLogger(__name__)


def create_invoice(db: Session, payload: CreateInvoiceRequest) -> Invoice:
    existing = db.query(Invoice).filter(Invoice.invoice_id == payload.invoice_id).first()
    if existing:
        logger.warning("Duplicate invoice attempt: %s", payload.invoice_id)
        raise DuplicateInvoiceError(payload.invoice_id)

    invoice = Invoice(
        invoice_id=payload.invoice_id,
        client_name=payload.client_name,
        client_email=str(payload.client_email),
        amount_due=payload.amount_due,
        due_date=payload.due_date,
        follow_up_count=payload.follow_up_count,
        current_stage=payload.current_stage,
        payment_status=payload.payment_status,
        last_followup_date=payload.last_followup_date,
    )
    db.add(invoice)
    try:
        db.commit()
        db.refresh(invoice)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to create invoice")
        raise DatabaseError("Failed to create invoice") from exc

    logger.info("Invoice created: %s", invoice.invoice_id)
    return invoice


def get_all_invoices(db: Session) -> list[Invoice]:
    return db.query(Invoice).order_by(Invoice.due_date.asc()).all()


def get_invoice_by_invoice_id(db: Session, invoice_id: str) -> Invoice:
    invoice = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    if not invoice:
        raise InvoiceNotFoundError(invoice_id)
    return invoice


def update_invoice(db: Session, invoice_id: str, payload: UpdateInvoiceRequest) -> Invoice:
    invoice = get_invoice_by_invoice_id(db, invoice_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(invoice, field, value)

    try:
        db.commit()
        db.refresh(invoice)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to update invoice: %s", invoice_id)
        raise DatabaseError("Failed to update invoice") from exc

    logger.info("Invoice updated: %s", invoice_id)
    return invoice


def delete_invoice(db: Session, invoice_id: str) -> Invoice:
    invoice = get_invoice_by_invoice_id(db, invoice_id)
    try:
        db.delete(invoice)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to delete invoice: %s", invoice_id)
        raise DatabaseError("Failed to delete invoice") from exc

    logger.info("Invoice deleted: %s", invoice_id)
    return invoice
