from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import JSON, Date, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.enums import EscalationStage, PaymentStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    follow_up_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_stage: Mapped[EscalationStage] = mapped_column(
        SAEnum(EscalationStage),
        default=EscalationStage.STAGE_1,
        nullable=False,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    last_followup_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_invoices_payment_status", "payment_status"),
        Index("ix_invoices_current_stage", "current_stage"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("invoices.invoice_id"),
        index=True,
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)
