from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TimeSeriesDataPoint(BaseModel):
    """Data point for time series data in analytics responses"""
    time: str = Field(..., description="Time point (hour format for 24h, date for 7d/30d)")
    count: int = Field(..., description="Count of conversations at this time point")


class HourlySessionDataPoint(BaseModel):
    """Data point for sessions by hour in analytics responses"""
    hour: str = Field(..., description="Hour of the day in 24-hour format (00-23)")
    count: int = Field(..., description="Count of sessions that started during this hour")


class DistributionDataPoint(BaseModel):
    """Data point for distribution analysis"""
    range: str = Field(..., description="Range bucket (e.g., '0-5s', '1-3m', '3-5', etc.)")
    count: int = Field(..., description="Count of items in this range")


class MessageDistributionDataPoint(BaseModel):
    """Data point for message count distribution analysis"""
    count: str = Field(..., description="Range of message counts (e.g., '1-2', '3-5', etc.)")
    sessions: int = Field(..., description="Number of sessions with this message count range")


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
    sessions_by_hour: List[HourlySessionDataPoint] = Field(
        ..., description="Aggregated count of sessions by hour of day (00-23)"
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
    response_rate: float = Field(
        ..., description="Percentage of user messages that received a successful bot response"
    )
    first_response_time_distribution: List[DistributionDataPoint] = Field(
        ..., description="Distribution of first response times in different time ranges"
    )
    session_duration_distribution: List[DistributionDataPoint] = Field(
        ..., description="Distribution of session durations in different time ranges"
    )
    messages_per_session_distribution: List[MessageDistributionDataPoint] = Field(
        ..., description="Distribution of number of messages per session"
    )
    last_updated: datetime = Field(..., description="Timestamp when the data was last refreshed")
