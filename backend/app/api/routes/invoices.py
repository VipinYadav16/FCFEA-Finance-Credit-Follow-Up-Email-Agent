from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_invoices_placeholder() -> dict[str, str]:
    return {"message": "Invoices endpoint placeholder"}
