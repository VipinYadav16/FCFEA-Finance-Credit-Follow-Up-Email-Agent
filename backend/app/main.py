import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.db.init_db import init_db
from app.utils.config import settings
from app.utils.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    logger = logging.getLogger(__name__)
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = jsonable_encoder(exc.errors())
        logger.warning("Validation failed for %s: %s", request.url.path, errors)
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    return app


app = create_app()
