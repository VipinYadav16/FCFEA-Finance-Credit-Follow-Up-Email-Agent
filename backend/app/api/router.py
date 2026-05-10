from fastapi import APIRouter

from app.api.routes import audit, health, invoices, workflows

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
