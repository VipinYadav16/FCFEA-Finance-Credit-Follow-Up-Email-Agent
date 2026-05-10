import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.enums import EscalationStage
from app.models.orm import Invoice
from app.models.schemas import WorkflowInvoiceContext, WorkflowRunSummary
from app.services import audit_service
from app.utils.exceptions import DatabaseError, WorkflowProcessingError
from app.utils.overdue import calculate_overdue_days, is_invoice_overdue
from app.workflows.engine import determine_escalation_stage

logger = logging.getLogger(__name__)


@dataclass
class WorkflowCounts:
    processed: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0


def build_workflow_context(invoice: Invoice) -> WorkflowInvoiceContext:
    overdue_days = calculate_overdue_days(invoice.due_date)
    return WorkflowInvoiceContext(
        invoice_id=invoice.invoice_id,
        client_name=invoice.client_name,
        client_email=invoice.client_email,
        amount_due=invoice.amount_due,
        due_date=invoice.due_date,
        overdue_days=overdue_days,
        escalation_stage=invoice.current_stage,
        payment_status=invoice.payment_status,
        follow_up_count=invoice.follow_up_count,
    )


def process_overdue_invoices(db: Session) -> WorkflowRunSummary:
    started_at = datetime.now(timezone.utc)
    counts = WorkflowCounts()
    updated_contexts: list[WorkflowInvoiceContext] = []

    invoices = db.query(Invoice).order_by(Invoice.due_date.asc()).all()
    logger.info("Workflow run started with %s invoices", len(invoices))

    for invoice in invoices:
        counts.processed += 1
        try:
            if not is_invoice_overdue(invoice.due_date):
                counts.skipped += 1
                continue

            overdue_days = calculate_overdue_days(invoice.due_date)
            new_stage = determine_escalation_stage(overdue_days)
            if new_stage == invoice.current_stage:
                counts.skipped += 1
                continue

            previous_stage = invoice.current_stage
            invoice.current_stage = new_stage
            try:
                db.add(invoice)
                db.commit()
                db.refresh(invoice)
            except SQLAlchemyError as exc:
                db.rollback()
                counts.errors += 1
                logger.exception("Workflow update failed for invoice %s", invoice.invoice_id)
                continue

            audit_service.create_audit_log(
                db,
                invoice_id=invoice.invoice_id,
                action_type="ESCALATION_STAGE_UPDATE",
                status="SUCCESS",
                metadata_json={
                    "previous_stage": previous_stage.value,
                    "new_stage": new_stage.value,
                    "overdue_days": overdue_days,
                },
            )

            updated_contexts.append(build_workflow_context(invoice))
            counts.updated += 1
            logger.info(
                "Invoice %s escalated from %s to %s (overdue=%s days)",
                invoice.invoice_id,
                previous_stage.value,
                new_stage.value,
                overdue_days,
            )
        except DatabaseError:
            counts.errors += 1
            logger.exception("Workflow update failed for invoice %s", invoice.invoice_id)
        except Exception as exc:  # noqa: BLE001
            counts.errors += 1
            logger.exception("Workflow processing failure for invoice %s", invoice.invoice_id)
            raise WorkflowProcessingError("Workflow processing failed") from exc

    stage_counts = {stage.value: 0 for stage in EscalationStage}
    overdue_count = 0
    escalated_count = 0
    legal_escalation_count = 0
    for invoice in invoices:
        stage_counts[invoice.current_stage.value] += 1
        if is_invoice_overdue(invoice.due_date):
            overdue_count += 1
        if invoice.current_stage != EscalationStage.STAGE_1:
            escalated_count += 1
        if invoice.current_stage == EscalationStage.LEGAL_ESCALATION:
            legal_escalation_count += 1

    finished_at = datetime.now(timezone.utc)
    logger.info(
        "Workflow run complete: processed=%s updated=%s skipped=%s errors=%s overdue=%s escalated=%s legal=%s",
        counts.processed,
        counts.updated,
        counts.skipped,
        counts.errors,
        overdue_count,
        escalated_count,
        legal_escalation_count,
    )
    return WorkflowRunSummary(
        started_at=started_at,
        finished_at=finished_at,
        processed_count=counts.processed,
        updated_count=counts.updated,
        skipped_count=counts.skipped,
        error_count=counts.errors,
        overdue_count=overdue_count,
        escalated_count=escalated_count,
        legal_escalation_count=legal_escalation_count,
        stage_counts=stage_counts,
        updated_invoices=updated_contexts,
    )


def get_overdue_invoices(db: Session) -> list[WorkflowInvoiceContext]:
    invoices = db.query(Invoice).order_by(Invoice.due_date.asc()).all()
    return [build_workflow_context(inv) for inv in invoices if is_invoice_overdue(inv.due_date)]


def get_escalated_invoices(db: Session) -> list[WorkflowInvoiceContext]:
    escalated = (
        db.query(Invoice)
        .filter(Invoice.current_stage != EscalationStage.STAGE_1)
        .order_by(Invoice.due_date.asc())
        .all()
    )
    return [build_workflow_context(inv) for inv in escalated]


def get_invoices_by_stage(db: Session, stage: EscalationStage) -> list[WorkflowInvoiceContext]:
    invoices = (
        db.query(Invoice)
        .filter(Invoice.current_stage == stage)
        .order_by(Invoice.due_date.asc())
        .all()
    )
    return [build_workflow_context(inv) for inv in invoices]
