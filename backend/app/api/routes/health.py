"""Service health endpoint."""

from fastapi import APIRouter

from app.api.dependencies import AsOfDependency
from app.api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Get service health")
def health(as_of: AsOfDependency) -> HealthResponse:
    """Return service status and the evaluation date of the loaded results."""
    return HealthResponse(status="ok", as_of=as_of)
