from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TimeSeriesDataPoint(BaseModel):
    """Data point for time series data in analytics responses"""
    time: str = Field(..., description="Time point (hour format for 24h, date for 7d/30d)")
    count: int = Field(..., description="Count of conversations at this time point")


class DashboardMetricsResponse(BaseModel):
    """Response model for dashboard analytics metrics"""
    success: bool = True
    data: Optional[dict] = None
    error: Optional[str] = None


class DashboardMetricsData(BaseModel):
    """Data model for dashboard analytics metrics"""
    total_conversations: int = Field(..., description="Total number of conversation sessions initiated")
    handoff_rate: float = Field(..., description="Percentage of conversations escalated to human agent")
    containment_rate: float = Field(..., description="Percentage of conversations fully handled by bot")
    conversations_by_time: List[TimeSeriesDataPoint] = Field(
        ..., description="Aggregated count of conversations by time period"
    )
    last_updated: datetime = Field(..., description="Timestamp when the data was last refreshed")


class BotEngagementMetricsResponse(BaseModel):
    """Response model for bot engagement metrics"""
    success: bool = True
    data: Optional[dict] = None
    error: Optional[str] = None


class BotEngagementMetricsData(BaseModel):
    """Data model for bot engagement metrics"""
    avg_session_duration: int = Field(
        ..., description="Average duration of chat sessions in seconds"
    )
    avg_messages_per_session: float = Field(
        ..., description="Average number of messages exchanged per session"
    )
    avg_resolution_time: int = Field(
        ..., description="Average time from conversation start to resolution in seconds"
    )
    first_response_time: int = Field(
        ..., description="Average time between user's first message and bot's first response in seconds"
    )
    last_updated: datetime = Field(..., description="Timestamp when the data was last refreshed")
