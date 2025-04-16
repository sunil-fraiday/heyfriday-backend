from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Literal

from app.services.analytics import AnalyticsService
from app.schemas.analytics import (
    DashboardMetricsResponse,
    BotEngagementMetricsResponse,
    DashboardMetricsData,
    BotEngagementMetricsData,
)
from app.utils.logger import get_logger
from app.api.v1.deps import verify_api_key

logger = get_logger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    time_period: Literal["24h", "7d", "30d"] = Query(..., description="Time period for metrics: 24h, 7d, or 30d"),
    api_key: str = Depends(verify_api_key)
) -> DashboardMetricsResponse:
    """
    Get dashboard analytics metrics for the specified time period.
    
    - **time_period**: Time period for which to fetch metrics. Valid values are 24h, 7d, or 30d.
    
    Returns dashboard metrics including:
    - Total conversations
    - Handoff rate (percentage of conversations escalated to human)
    - Containment rate (percentage of conversations handled by bot)
    - Conversations by time (hourly for 24h, daily for 7d/30d)
    """
    try:
        logger.info(f"Fetching dashboard metrics for time period: {time_period}")
        metrics_data = AnalyticsService.get_dashboard_metrics(time_period)
        return DashboardMetricsResponse(success=True, data=metrics_data.model_dump())
    except ValueError as e:
        logger.error(f"Invalid time period: {time_period}")
        return DashboardMetricsResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception(f"Error calculating dashboard metrics: {str(e)}")
        return DashboardMetricsResponse(success=False, error="An error occurred while calculating metrics")


@router.get("/bot-engagement", response_model=BotEngagementMetricsResponse)
async def get_bot_engagement_metrics(
    time_period: Literal["24h", "7d", "30d"] = Query(..., description="Time period for metrics: 24h, 7d, or 30d"),
    api_key: str = Depends(verify_api_key)
) -> BotEngagementMetricsResponse:
    """
    Get bot engagement metrics for the specified time period.
    
    - **time_period**: Time period for which to fetch metrics. Valid values are 24h, 7d, or 30d.
    
    Returns bot engagement metrics including:
    - Average session duration (in seconds)
    - Average messages per session
    - Average resolution time (in seconds)
    - First response time (in seconds)
    """
    try:
        logger.info(f"Fetching bot engagement metrics for time period: {time_period}")
        metrics_data = AnalyticsService.get_bot_engagement_metrics(time_period)
        return BotEngagementMetricsResponse(success=True, data=metrics_data.model_dump())
    except ValueError as e:
        logger.error(f"Invalid time period: {time_period}")
        return BotEngagementMetricsResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception(f"Error calculating bot engagement metrics: {str(e)}")
        return BotEngagementMetricsResponse(success=False, error="An error occurred while calculating metrics")
