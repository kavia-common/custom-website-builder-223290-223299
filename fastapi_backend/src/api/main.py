from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter

# Import versioned API router
from .routes.generation import router as generation_router

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

# Root health check
@app.get("/", tags=["Health"], summary="Health Check")
def health_check():
    """Return a simple health check message indicating the API is running."""
    return {"message": "Healthy"}

# API usage note for WebSocket (not used currently) to keep docs explicit
@app.get(
    "/api/v1/docs-info",
    tags=["Health"],
    summary="API usage notes",
    description="This API currently exposes REST endpoints only. No WebSocket interfaces are used.",
)
def docs_info():
    """Provide a brief usage note for clients browsing the docs."""
    return {"websocket": False, "notes": "Use REST endpoints under /api/v1."}

# Mount versioned API router at /api/v1
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(generation_router)
app.include_router(api_v1)
