from fastapi import APIRouter

# PUBLIC_INTERFACE
def get_router() -> APIRouter:
    """Return the APIRouter for generation endpoints.

    This function exists to provide a clear public interface for retrieving
    the generation router and to facilitate testing/importing without side effects.
    """
    router = APIRouter(prefix="/generation", tags=["Generation"])

    @router.get(
        "/",
        summary="List generation capabilities",
        description="Placeholder endpoint to list available generation capabilities and API contract.",
        operation_id="generation_list_capabilities",
        responses={200: {"description": "Successful Response"}},
    )
    def list_capabilities():
        """Return a placeholder response describing generation capabilities."""
        return {
            "message": "Generation API surface is available.",
            "endpoints": [
                "POST /api/v1/generation/requests",
                "GET /api/v1/generation/preview/{request_id}",
            ],
        }

    return router


# Expose router instance for easy import in app
router = get_router()
