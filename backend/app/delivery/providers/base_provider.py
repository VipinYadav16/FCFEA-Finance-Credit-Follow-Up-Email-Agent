from abc import ABC, abstractmethod

from app.models.schemas import GeneratedEmailPreviewResponse


class BaseDeliveryProvider(ABC):
    @abstractmethod
    def send(self, invoice_id: str, preview: GeneratedEmailPreviewResponse) -> dict:
        """Execute delivery action and return operational metadata."""
