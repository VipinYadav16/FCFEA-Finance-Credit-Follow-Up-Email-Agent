from datetime import datetime, timezone

from app.delivery.providers.dry_run_provider import DryRunDeliveryProvider
from app.models.enums import EscalationStage
from app.models.schemas import GeneratedEmailPreviewResponse


def test_dry_run_provider_returns_simulated_metadata() -> None:
    provider = DryRunDeliveryProvider()
    preview = GeneratedEmailPreviewResponse(
        id=1,
        invoice_id="INV-101",
        escalation_stage=EscalationStage.STAGE_2,
        tone_used="professional reminder",
        subject="Reminder INV-101",
        email_body="Invoice INV-101 amount 150.00 due 2026-05-01 is pending.",
        content_summary="summary",
        generated_at=datetime.now(timezone.utc),
    )
    metadata = provider.send("INV-101", preview)
    assert metadata["delivery_mode"] == "DRY_RUN"
    assert metadata["status"] == "SIMULATED"
    assert metadata["invoice_id"] == "INV-101"
