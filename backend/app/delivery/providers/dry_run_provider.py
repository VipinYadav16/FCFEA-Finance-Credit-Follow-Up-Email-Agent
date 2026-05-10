from datetime import datetime, timezone

from app.delivery.providers.base_provider import BaseDeliveryProvider
from app.models.schemas import GeneratedEmailPreviewResponse


class DryRunDeliveryProvider(BaseDeliveryProvider):
    def send(self, invoice_id: str, preview: GeneratedEmailPreviewResponse) -> dict:
        return {
            "delivery_mode": "DRY_RUN",
            "invoice_id": invoice_id,
            "subject": preview.subject,
            "simulated_recipient": f"masked:{preview.invoice_id}",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "status": "SIMULATED",
        }
