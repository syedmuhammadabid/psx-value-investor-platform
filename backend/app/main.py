"""FastAPI application entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.jobs.scheduler import scheduler


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Start background jobs on startup; stop them cleanly on shutdown."""
    scheduler.start()
    logging.getLogger("app").info("scheduler started — daily price sync at 17:00 PKT (12:00 UTC)")
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        logging.getLogger("app").info("scheduler stopped")


def create_app() -> FastAPI:
    """Application factory."""
    configure_logging()
    logging.getLogger("app").info("starting %s v%s", settings.project_name, settings.version)

    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=_lifespan,
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
