from __future__ import annotations

import logging
import traceback
import uuid
from typing import Any, Dict, Optional, cast

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

# Configure a basic module-level logger. In production, configure via logging config.
logger = logging.getLogger("api")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# PUBLIC_INTERFACE
class DomainError(Exception):
    """Base domain error for predictable business rule violations.

    Attributes:
        code: A machine-readable error code (e.g., 'INVALID_PAGES')
        message: Human-friendly description of the error.
        status_code: HTTP status to respond with (default 400).
        details: Optional details payload to help clients fix issues.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class _ErrorBody(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    requestId: str


class _Envelope(BaseModel):
    error: _ErrorBody


def _get_or_create_request_id(request: Request) -> str:
    """Fetch X-Request-ID from headers or generate a UUID4."""
    rid = request.headers.get("X-Request-ID") or request.headers.get("x-request-id")
    if rid and isinstance(rid, str) and rid.strip():
        return rid.strip()
    return str(uuid.uuid4())


def _response_with_request_id(
    request: Request, status: int, payload: Dict[str, Any], request_id: str
) -> JSONResponse:
    headers = {"X-Request-ID": request_id}
    return JSONResponse(content=payload, status_code=status, headers=headers)


# PUBLIC_INTERFACE
def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    """FastAPI exception handler for DomainError returning structured error payloads."""
    request_id = _get_or_create_request_id(request)
    body = _Envelope(
        error=_ErrorBody(
            code=exc.code,
            message=exc.message,
            details=exc.details or None,
            requestId=request_id,
        )
    ).model_dump()
    # Log at warning level for domain errors
    logger.warning(
        "DomainError code=%s status=%s request_id=%s details=%s path=%s",
        exc.code,
        exc.status_code,
        request_id,
        exc.details,
        request.url.path,
    )
    return _response_with_request_id(request, exc.status_code, body, request_id)


# PUBLIC_INTERFACE
def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
    """FastAPI exception handler for Pydantic ValidationError (422)."""
    request_id = _get_or_create_request_id(request)
    # Normalize errors into a concise structure
    error_details: Dict[str, Any] = {"errors": cast(Any, exc.errors())}
    body = _Envelope(
        error=_ErrorBody(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=error_details,
            requestId=request_id,
        )
    ).model_dump()
    logger.info(
        "ValidationError status=%s request_id=%s path=%s errors=%d",
        HTTP_422_UNPROCESSABLE_ENTITY,
        request_id,
        request.url.path,
        len(error_details.get("errors", [])),
    )
    return _response_with_request_id(request, HTTP_422_UNPROCESSABLE_ENTITY, body, request_id)


# PUBLIC_INTERFACE
def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all FastAPI exception handler to avoid leaking stack traces to clients."""
    request_id = _get_or_create_request_id(request)
    body = _Envelope(
        error=_ErrorBody(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred.",
            details=None,
            requestId=request_id,
        )
    ).model_dump()
    # Log full traceback for diagnostics
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error(
        "Unhandled exception request_id=%s path=%s\n%s",
        request_id,
        request.url.path,
        tb,
    )
    return _response_with_request_id(request, HTTP_500_INTERNAL_SERVER_ERROR, body, request_id)


# PUBLIC_INTERFACE
def make_error_response(
    request: Request,
    *,
    code: str,
    message: str,
    status_code: int = HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Helper to create a structured error response for ad-hoc error returns."""
    request_id = _get_or_create_request_id(request)
    body = _Envelope(
        error=_ErrorBody(
            code=code,
            message=message,
            details=details or None,
            requestId=request_id,
        )
    ).model_dump()
    logger.warning(
        "AdHoc error code=%s status=%s request_id=%s path=%s",
        code,
        status_code,
        request_id,
        request.url.path,
    )
    return _response_with_request_id(request, status_code, body, request_id)
