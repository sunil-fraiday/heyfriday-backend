from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime

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
    start_time: datetime = Query(..., description="Start date and time (UTC) for metrics."),
    end_time: Optional[datetime] = Query(None, description="End date and time (UTC) for metrics. If not provided, defaults to current time."),
    api_key: str = Depends(verify_api_key)
) -> DashboardMetricsResponse:
    """
    Get dashboard analytics metrics for the specified time range.
    
    - **start_time**: Start date and time (UTC) for metrics.
    - **end_time**: End date and time (UTC) for metrics. If not provided, defaults to current time.
    
    Returns dashboard metrics including:
    - Total conversations
    - Handoff rate (percentage of conversations escalated to human)
    - Containment rate (percentage of conversations handled by bot)
    - Conversations by time (hourly for short ranges, daily for longer ranges)
    """
    try:
        logger.info(f"Fetching dashboard metrics for time range: {start_time} to {end_time or 'now'}")
            
        metrics_data = AnalyticsService.get_dashboard_metrics(
            start_date=start_time, 
            end_date=end_time
        )
        return DashboardMetricsResponse(success=True, data=metrics_data.model_dump())
    except ValueError as e:
        logger.error(f"Invalid parameters: {str(e)}")
        return DashboardMetricsResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception(f"Error calculating dashboard metrics: {str(e)}")
        return DashboardMetricsResponse(success=False, error="An error occurred while calculating metrics")


@router.get("/bot-engagement", response_model=BotEngagementMetricsResponse)
async def get_bot_engagement_metrics(
    start_time: datetime = Query(..., description="Start date and time (UTC) for metrics."),
    end_time: Optional[datetime] = Query(None, description="End date and time (UTC) for metrics. If not provided, defaults to current time."),
    api_key: str = Depends(verify_api_key)
) -> BotEngagementMetricsResponse:
    """
    Get bot engagement metrics for the specified time range.
    
    - **start_time**: Start date and time (UTC) for metrics.
    - **end_time**: End date and time (UTC) for metrics. If not provided, defaults to current time.
    
    Returns bot engagement metrics including:
    - Average session duration (in seconds)
    - Average messages per session
    - Average resolution time (in seconds)
    - First response time (in seconds)
    """
    try:
        logger.info(f"Fetching bot engagement metrics for time range: {start_time} to {end_time or 'now'}")
            
        metrics_data = AnalyticsService.get_bot_engagement_metrics(
            start_date=start_time, 
            end_date=end_time
        )
        return BotEngagementMetricsResponse(success=True, data=metrics_data.model_dump())
    except ValueError as e:
        logger.error(f"Invalid parameters: {str(e)}")
        return BotEngagementMetricsResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception(f"Error calculating bot engagement metrics: {str(e)}")
        return BotEngagementMetricsResponse(success=False, error="An error occurred while calculating metrics")
