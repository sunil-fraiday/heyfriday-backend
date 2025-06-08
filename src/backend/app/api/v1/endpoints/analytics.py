from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime, timedelta, timezone

from app.services.analytics import AnalyticsService
from app.schemas.analytics import (
    DashboardMetricsResponse,
    BotEngagementMetricsResponse,
    DashboardMetricsData,
    BotEngagementMetricsData,
    ContainmentRateResponse
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


@router.get("/containment-rate", response_model=ContainmentRateResponse)
async def get_containment_rate_metrics(
    start_date: datetime = Query(..., description="Start date and time (UTC) for metrics.", alias="start_date"),
    end_date: Optional[datetime] = Query(None, description="End date and time (UTC) for metrics. If not provided, defaults to current time.", alias="end_date"),
    aggregation: str = Query(
        "auto",
        description="Time aggregation level. One of: auto, hour, day, week, month",
        regex="^(auto|hour|day|week|month)$"
    ),
    api_key: str = Depends(verify_api_key)
) -> ContainmentRateResponse:
    """
    Get containment rate metrics over time.
    
    - **start_time**: Start date and time (UTC) for metrics.
    - **end_time**: End date and time (UTC) for metrics. If not provided, defaults to current time.
    - **aggregation**: Time aggregation level. One of: auto, hour, day, week, month.
      - auto: Automatically selects the most appropriate aggregation based on time range.
    
    Returns time-series data of containment rates (percentage of conversations fully handled by the bot).
    """
    try:
        logger.info(
            f"Fetching containment rate metrics for time range: {start_date} to {end_date or 'now'}, "
            f"aggregation: {aggregation}"
        )
        
        metrics_data = AnalyticsService.get_containment_rate_metrics(
            start_date=start_date,
            end_date=end_date,
            aggregation=aggregation
        )
        
        return ContainmentRateResponse(
            success=True,
            data=metrics_data["data"],
            metadata=metrics_data["metadata"]
        )
    except ValueError as e:
        logger.error(f"Invalid parameters: {str(e)}")
        return ContainmentRateResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception(f"Error calculating containment rate metrics: {str(e)}")
        return ContainmentRateResponse(
            success=False,
            error="An error occurred while calculating containment rate metrics"
        )
