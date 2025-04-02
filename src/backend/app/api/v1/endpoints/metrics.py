from fastapi import APIRouter, Response
from app.services.metrics import MetricsService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Metrics"])


@router.get("/metrics", response_class=Response)
async def metrics():
    """
    Endpoint that exposes Prometheus metrics.
    This endpoint is scraped by Prometheus to collect metrics about the application.
    """
    logger.debug("Metrics endpoint called")
    metrics_data = MetricsService.get_metrics()
    return Response(content=metrics_data, media_type="text/plain")
