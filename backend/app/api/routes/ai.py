from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.schemas import (
    AIBatchGenerateRequest,
    AIBatchGenerateResponse,
    AIEmailGenerationResponse,
    GeneratedEmailPreviewResponse,
)
from app.services import ai_generation_service, ai_preview_service
from app.utils.exceptions import (
    AIOutputValidationError,
    AIProviderError,
    DatabaseError,
    InvoiceNotFoundError,
    PromptLoadError,
)

router = APIRouter()


def _is_quota_or_rate_limited(message: str) -> bool:
    normalized = message.lower()
    signals = [
        "quota",
        "rate limit",
        "429",
        "resourceexhausted",
        "too many requests",
    ]
    return any(token in normalized for token in signals)


@router.post("/generate/{invoice_id}", response_model=AIEmailGenerationResponse)
def generate_invoice_email(invoice_id: str, db: Session = Depends(get_db)) -> AIEmailGenerationResponse:
    try:
        return ai_generation_service.generate_followup_email(db, invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (AIOutputValidationError, PromptLoadError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except AIProviderError as exc:
        if _is_quota_or_rate_limited(str(exc)):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI provider quota/rate limit reached. Retry later or use another provider key.",
            ) from exc
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except DatabaseError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/generate-overdue-batch", response_model=AIBatchGenerateResponse)
def generate_overdue_batch(
    request: AIBatchGenerateRequest, db: Session = Depends(get_db)
) -> AIBatchGenerateResponse:
    items, failures = ai_generation_service.generate_overdue_batch(db, request.limit)
    return AIBatchGenerateResponse(
        generated_count=len(items),
        failed_count=len(failures),
        items=items,
        failures=failures,
    )


@router.get("/generated-preview/{invoice_id}", response_model=GeneratedEmailPreviewResponse)
def get_generated_preview(invoice_id: str, db: Session = Depends(get_db)) -> GeneratedEmailPreviewResponse:
    preview = ai_preview_service.get_latest_preview_by_invoice_id(db, invoice_id)
    if preview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No generated preview found for invoice '{invoice_id}'",
        )
    return GeneratedEmailPreviewResponse.model_validate(preview)
