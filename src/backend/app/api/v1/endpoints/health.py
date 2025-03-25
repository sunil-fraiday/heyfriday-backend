from fastapi import APIRouter, Response, status
from typing import Dict, Any

from app.services.health import HealthService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint to verify the service is running.
    Used for simple monitoring and basic availability checks.
    """
    return await HealthService.check_health()


@router.get("/readiness")
async def readiness_check(response: Response) -> Dict[str, Any]:
    """
    Readiness check endpoint to verify if the service is ready to accept traffic.
    Checks all required dependencies like database and message broker.
    """
    readiness = await HealthService.get_readiness()

    if readiness["status"] != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return readiness


@router.get("/healthz", include_in_schema=False)
async def kubernetes_health_check() -> Dict[str, str]:
    """
    Simplified health check for Kubernetes.
    This endpoint follows Kubernetes probe naming conventions.
    """
    return {"status": "healthy"}


@router.get("/health/full", include_in_schema=False)
async def full_health_check(response: Response) -> Dict[str, Any]:
    """
    Detailed health check that includes all system components.
    Primarily used for debugging and monitoring.
    """
    health_info = await HealthService.get_full_health()

    if not health_info.get("ready", False):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return health_info
