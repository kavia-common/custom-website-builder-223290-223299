from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter

# Import versioned API router
from .routes.generation import router as generation_router
from .errors import (
    handle_unexpected_error,
    handle_validation_error,
    handle_domain_error,
)
from .errors import DomainError  # re-export type for potential external use
from pydantic import ValidationError

openapi_tags = [
    {
        "name": "Health",
        "description": "Service health and operational endpoints.",
    },
    {
        "name": "Generation",
        "description": "Endpoints for requesting and previewing website generation.",
    },
]

app = FastAPI(
    title="Custom Website Builder API",
    description=(
        "Backend service that receives user input and requirements to generate a "
        "custom website based on the user's idea and project details."
    ),
    version="0.1.0",
    openapi_tags=openapi_tags,
)

# CORS settings - permissive for development; restrict in production via env
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware: propagate/generate X-Request-ID for all responses
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    # Read header or generate a simple UUID using the helper in handler by importing lazily
    # To avoid circular import, duplicate small logic here.
    rid = request.headers.get("X-Request-ID") or request.headers.get("x-request-id")
    if not rid or not rid.strip():
        import uuid

        rid = str(uuid.uuid4())

    # Proceed
    response = await call_next(request)
    # Ensure header is set on all responses
    response.headers["X-Request-ID"] = rid
    return response


# Register global exception handlers
app.add_exception_handler(ValidationError, handle_validation_error)
app.add_exception_handler(DomainError, handle_domain_error)
app.add_exception_handler(Exception, handle_unexpected_error)

# Root health check
@app.get("/", tags=["Health"], summary="Health Check")
def health_check(request: Request):
    """Return a simple health check message indicating the API is running."""
    # Ensure response carries X-Request-ID (middleware will also add it)
    return {"message": "Healthy"}

# API usage note for WebSocket (not used currently) to keep docs explicit
@app.get(
    "/api/v1/docs-info",
    tags=["Health"],
    summary="API usage notes",
    description=(
        "This API currently exposes REST endpoints only. No WebSocket interfaces are used.\n\n"
        "All responses include an X-Request-ID header for correlation. Errors are returned in the shape:\n"
        "{ \"error\": { \"code\": string, \"message\": string, \"details\": object|null, \"requestId\": string } }."
    ),
)
def docs_info(request: Request):
    """Provide a brief usage note for clients browsing the docs."""
    return {"websocket": False, "notes": "Use REST endpoints under /api/v1."}

# Mount versioned API router at /api/v1
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(generation_router)
app.include_router(api_v1)
