from fastapi import APIRouter

from app.utils.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
