"""RFC 7807 problem+json error handling."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

PROBLEM_JSON = "application/problem+json"


def _problem(
    *, status: int, title: str, detail: str, instance: str, type_: str = "about:blank"
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type=PROBLEM_JSON,
        content={
            "type": type_,
            "title": title,
            "status": status,
            "detail": detail,
            "instance": instance,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register handlers that return RFC 7807 problem+json responses."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem(
            status=exc.status_code,
            title=exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            detail=exc.detail if isinstance(exc.detail, str) else "",
            instance=request.url.path,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _problem(
            status=422,
            title="Validation Error",
            detail=f"{len(exc.errors())} request parameter(s) failed validation.",
            instance=request.url.path,
            type_="https://httpstatuses.com/422",
        )
