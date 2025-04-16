from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List, Tuple, Optional

from app.models.mongodb.chat_session import ChatSession
from app.models.mongodb.chat_message import ChatMessage, SenderType
from app.models.mongodb.events.event import Event
from app.models.mongodb.events.event_types import EventType
from app.schemas.analytics import (
    DashboardMetricsData,
    BotEngagementMetricsData,
    TimeSeriesDataPoint,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for calculating analytics metrics"""

    @staticmethod
    def _get_time_range(time_period: str) -> Tuple[datetime, datetime]:
        """
        Get start and end datetime objects based on the time period.
        
        Args:
            time_period: One of '24h', '7d', or '30d'
            
        Returns:
            Tuple of (start_datetime, end_datetime)
        """
        now = datetime.now(timezone.utc)
        
        if time_period == "24h":
            start_time = now - timedelta(hours=24)
        elif time_period == "7d":
            start_time = now - timedelta(days=7)
        elif time_period == "30d":
            start_time = now - timedelta(days=30)
        else:
            raise ValueError(f"Invalid time period: {time_period}. Valid values are '24h', '7d', or '30d'")
            
        return start_time, now

    @staticmethod
    def get_dashboard_metrics(time_period: str) -> DashboardMetricsData:
        """
        Calculate dashboard metrics for the specified time period.
        
        Args:
            time_period: One of '24h', '7d', or '30d'
            
        Returns:
            DashboardMetricsData object with calculated metrics
        """
        start_time, end_time = AnalyticsService._get_time_range(time_period)
        
        # Get total conversations in the time period
        total_conversations = ChatSession.objects(
            created_at__gte=start_time,
            created_at__lte=end_time
        ).count()
        
        # Get handoff events
        handoff_events = Event.objects(
            event_type=EventType.CHAT_WORKFLOW_HANDOVER.value,
            created_at__gte=start_time,
            created_at__lte=end_time
        )
        
        # Calculate handoff and containment rates
        handoff_count = handoff_events.count()
        handoff_rate = (handoff_count / total_conversations * 100) if total_conversations > 0 else 0
        containment_rate = 100 - handoff_rate
        
        # Get conversations by time
        conversations_by_time = AnalyticsService._get_conversations_by_time(time_period, start_time, end_time)
        
        return DashboardMetricsData(
            total_conversations=total_conversations,
            handoff_rate=round(handoff_rate, 1),
            containment_rate=round(containment_rate, 1),
            conversations_by_time=conversations_by_time,
            last_updated=datetime.now(timezone.utc)
        )

    @staticmethod
    def _get_conversations_by_time(time_period: str, start_time: datetime, end_time: datetime) -> List[TimeSeriesDataPoint]:
        """
        Get conversation counts grouped by time periods.
        
        Args:
            time_period: One of '24h', '7d', or '30d'
            start_time: Start datetime for the query
            end_time: End datetime for the query
            
        Returns:
            List of TimeSeriesDataPoint objects
        """
        result = []
        
        if time_period == "24h":
            # Group by hour for 24h period
            for hour in range(24):
                # Calculate the hour boundaries in UTC
                hour_start = end_time.replace(minute=0, second=0, microsecond=0) - timedelta(hours=24-hour)
                hour_end = hour_start + timedelta(hours=1)
                
                # Format as "H:00" in UTC
                hour_label = f"{hour_start.hour}:00"
                
                # Query for sessions created in this hour
                count = ChatSession.objects(
                    created_at__gte=hour_start,
                    created_at__lt=hour_end
                ).count()
                
                result.append(TimeSeriesDataPoint(time=hour_label, count=count))
                
                # Log for debugging
                logger.debug(f"Hour {hour_label}: {hour_start} to {hour_end}, count: {count}")
        else:
            # Group by day for 7d or 30d periods
            days = 7 if time_period == "7d" else 30
            
            for day in range(days):
                # Calculate day boundaries in UTC
                day_start = (start_time + timedelta(days=day)).replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                
                # Format as "YYYY-MM-DD"
                day_label = day_start.strftime("%Y-%m-%d")
                
                # Query for sessions created on this day
                count = ChatSession.objects(
                    created_at__gte=day_start,
                    created_at__lt=day_end
                ).count()
                
                result.append(TimeSeriesDataPoint(time=day_label, count=count))
                
                # Log for debugging
                logger.debug(f"Day {day_label}: {day_start} to {day_end}, count: {count}")
                
        return result

    @staticmethod
    def get_bot_engagement_metrics(time_period: str) -> BotEngagementMetricsData:
        """
        Calculate bot engagement metrics for the specified time period.
        
        Args:
            time_period: One of '24h', '7d', or '30d'
            
        Returns:
            BotEngagementMetricsData object with calculated metrics
        """
        start_time, end_time = AnalyticsService._get_time_range(time_period)
        
        # Get chat sessions in the time period
        chat_sessions = ChatSession.objects(
            created_at__gte=start_time,
            created_at__lte=end_time
        )
        
        total_sessions = chat_sessions.count()
        
        if total_sessions == 0:
            return BotEngagementMetricsData(
                avg_session_duration=0,
                avg_messages_per_session=0,
                avg_resolution_time=0,
                first_response_time=0,
                last_updated=datetime.now(timezone.utc)
            )
        
        # Calculate metrics for each session
        total_duration = 0
        total_messages = 0
        total_resolution_time = 0
        total_first_response_time = 0
        sessions_with_first_response = 0
        
        for session in chat_sessions:
            # Get messages for this session
            messages = ChatMessage.objects(session=session).order_by('created_at')
            message_count = messages.count()
            
            if message_count > 0:
                # Calculate session duration (time between first and last message)
                first_message = messages.first()
                last_message = messages.order_by('-created_at').first()
                
                if first_message and last_message:
                    session_duration = (last_message.created_at - first_message.created_at).total_seconds()
                    total_duration += session_duration
                    total_resolution_time += session_duration
                
                # Count messages in this session
                total_messages += message_count
                
                # Calculate first response time
                first_user_message = messages.filter(sender_type=SenderType.USER.value).first()
                if first_user_message:
                    first_bot_response = messages.filter(
                        sender_type=SenderType.ASSISTANT.value,
                        created_at__gt=first_user_message.created_at
                    ).first()
                    
                    if first_bot_response:
                        first_response_time = (first_bot_response.created_at - first_user_message.created_at).total_seconds()
                        total_first_response_time += first_response_time
                        sessions_with_first_response += 1
        
        # Calculate averages
        avg_session_duration = int(total_duration / total_sessions) if total_sessions > 0 else 0
        avg_messages_per_session = round(total_messages / total_sessions, 1) if total_sessions > 0 else 0
        avg_resolution_time = int(total_resolution_time / total_sessions) if total_sessions > 0 else 0
        avg_first_response_time = int(total_first_response_time / sessions_with_first_response) if sessions_with_first_response > 0 else 0
        
        return BotEngagementMetricsData(
            avg_session_duration=avg_session_duration,
            avg_messages_per_session=avg_messages_per_session,
            avg_resolution_time=avg_resolution_time,
            first_response_time=avg_first_response_time,
            last_updated=datetime.now(timezone.utc)
        )
