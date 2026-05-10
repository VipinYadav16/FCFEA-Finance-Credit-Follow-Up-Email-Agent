from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_audit_placeholder() -> dict[str, str]:
    return {"message": "Audit endpoint placeholder"}
