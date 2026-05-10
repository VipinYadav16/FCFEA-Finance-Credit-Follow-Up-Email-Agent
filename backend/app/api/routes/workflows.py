from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_workflows_placeholder() -> dict[str, str]:
    return {"message": "Workflows endpoint placeholder"}
