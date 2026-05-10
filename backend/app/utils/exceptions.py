class AppError(Exception):
    """Base application exception."""


class DuplicateInvoiceError(AppError):
    def __init__(self, invoice_id: str) -> None:
        super().__init__(f"Invoice '{invoice_id}' already exists")
        self.invoice_id = invoice_id


class InvoiceNotFoundError(AppError):
    def __init__(self, invoice_id: str) -> None:
        super().__init__(f"Invoice '{invoice_id}' not found")
        self.invoice_id = invoice_id


class DatabaseError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class WorkflowProcessingError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidWorkflowStateError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AIProviderError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AIOutputValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class PromptLoadError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class DeliveryStateError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class DeliveryNotFoundError(AppError):
    def __init__(self, invoice_id: str) -> None:
        super().__init__(f"No delivery record found for invoice '{invoice_id}'")
