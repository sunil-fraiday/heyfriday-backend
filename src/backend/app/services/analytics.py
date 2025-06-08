from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor

from app.models.mongodb.chat_session import ChatSession
from app.models.mongodb.chat_message import ChatMessage, SenderType
from app.models.mongodb.events.event import Event
from app.models.mongodb.events.event_types import EventType
from app.schemas.analytics import (
    DashboardMetricsData,
    BotEngagementMetricsData,
    TimeSeriesDataPoint,
    HourlySessionDataPoint,
    DistributionDataPoint,
    MessageDistributionDataPoint,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for calculating analytics metrics"""

    @staticmethod
    def _get_time_range(start_date: datetime, end_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """
        Get start and end datetime objects based on the provided dates.
        
        Args:
            start_date: Start datetime (UTC) for the time range.
            end_date: End datetime (UTC) for the time range. If not provided, defaults to current time.
            
        Returns:
            Tuple of (start_datetime, end_datetime)
        """
        now = datetime.now(timezone.utc)
        
        # If end_date not provided, use current time
        actual_end_date = end_date if end_date is not None else now
        return start_date, actual_end_date

    @staticmethod
    def get_dashboard_metrics(start_date: datetime, end_date: Optional[datetime] = None) -> DashboardMetricsData:
        """
        Calculate dashboard metrics for the specified time range.
        
        Args:
            start_date: Start datetime (UTC) for the time range.
            end_date: End datetime (UTC) for the time range. If not provided, defaults to current time.
            
        Returns:
            DashboardMetricsData object with calculated metrics
        """
        start_time, end_time = AnalyticsService._get_time_range(start_date, end_date)
        
        # Get total conversations in the time period
        total_conversations = ChatSession.objects(
            created_at__gte=start_time,
            created_at__lte=end_time
        ).count()
        
        # Use MongoDB aggregation pipeline to count unique parent_ids efficiently
        # This avoids loading all distinct values into application memory
        try:
            pipeline_result = Event._get_collection().aggregate([
                {"$match": {
                    "event_type": EventType.CHAT_WORKFLOW_HANDOVER.value,
                    "created_at": {"$gte": start_time, "$lte": end_time},
                    "parent_id": {"$exists": True}
                }},
                {"$group": {"_id": "$parent_id"}},
                {"$count": "count"}
            ])
            
            # Get the count from the pipeline result
            result_doc = next(pipeline_result, {"count": 0})
            unique_sessions_with_handovers = result_doc.get("count", 0)
        except Exception as e:
            logger.error(f"Error in aggregation pipeline: {e}")
            unique_sessions_with_handovers = 0
        
        # Calculate handoff and containment rates based on unique sessions with handovers
        handoff_rate = (unique_sessions_with_handovers / total_conversations * 100) if total_conversations > 0 else 0
        containment_rate = 100 - handoff_rate
        
        # Log for debugging
        logger.debug(f"Total conversations: {total_conversations}, Unique sessions with handovers: {unique_sessions_with_handovers}")
        
        # Get conversations by time
        conversations_by_time = AnalyticsService._get_conversations_by_time(start_time, end_time)
        
        # Get sessions by hour
        sessions_by_hour = AnalyticsService._get_sessions_by_hour(start_time, end_time)
        
        return DashboardMetricsData(
            total_conversations=total_conversations,
            handoff_rate=round(handoff_rate, 1),
            containment_rate=round(containment_rate, 1),
            conversations_by_time=conversations_by_time,
            sessions_by_hour=sessions_by_hour,
            last_updated=datetime.now(timezone.utc)
        )

    @staticmethod
    def _get_conversations_by_time(start_time: datetime, end_time: datetime) -> List[TimeSeriesDataPoint]:
        """
        Get conversation counts grouped by time periods.
        
        Args:
            start_time: Start datetime for the query
            end_time: End datetime for the query
            
        Returns:
            List of TimeSeriesDataPoint objects
        """
        result = []
        
        # Calculate the time delta between start and end
        time_delta = end_time - start_time
        time_delta_hours = time_delta.total_seconds() / 3600
        
        # Decide grouping based on the time range
        # For ranges less than 48 hours, group by hour
        # For ranges between 2 days and 60 days, group by day
        # For longer ranges, group by week or month (future enhancement)
        
        if time_delta_hours <= 48:
            # Group by hour
            # Calculate the number of complete hours in the range
            num_hours = int(time_delta_hours) + 1  # Add 1 to include partial hour
            
            # Limit to a reasonable number of data points
            if num_hours > 48:
                num_hours = 48
                
            for hour in range(num_hours):
                # Calculate hour boundaries in UTC
                hour_start = end_time.replace(minute=0, second=0, microsecond=0) - timedelta(hours=num_hours-hour)
                hour_end = hour_start + timedelta(hours=1)
                
                # Ensure we don't go before the actual start time
                if hour_start < start_time:
                    hour_start = start_time
                
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
            # Group by day
            # Calculate the number of days in the range
            days_delta = (end_time.date() - start_time.date()).days + 1  # Add 1 to include partial day
            
            # Limit to a reasonable number of data points (cap at 90 days)
            if days_delta > 90:
                days_delta = 90
            
            for day in range(days_delta):
                # Calculate day boundaries in UTC
                day_start = (start_time + timedelta(days=day)).replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Ensure we don't start before the actual start time
                if day == 0 and day_start < start_time:
                    day_start = start_time
                    
                day_end = (day_start + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Ensure we don't go past the end time
                if day_end > end_time:
                    day_end = end_time
                
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
    def get_containment_rate_metrics(
        start_date: datetime,
        end_date: Optional[datetime] = None,
        aggregation: str = "auto"
    ) -> Dict:
        """
        Calculate containment rate metrics for the specified time range.
        
        Args:
            start_date: Start datetime (UTC) for the time range.
            end_date: End datetime (UTC) for the time range. If not provided, defaults to current time.
            aggregation: Time aggregation level ("auto", "hour", "day", "week", "month")
            
        Returns:
            Dictionary containing containment rate data points and metadata
        """
        start_time, end_time = AnalyticsService._get_time_range(start_date, end_date)
        time_delta = end_time - start_time
        time_delta_hours = time_delta.total_seconds() / 3600
        
        # Determine the appropriate aggregation level
        if aggregation == "auto":
            if time_delta_hours <= 48:
                aggregation = "hour"
            elif time_delta_hours <= 14 * 24:  # 14 days
                aggregation = "day"
            elif time_delta_hours <= 60 * 24:  # 60 days
                aggregation = "week"
            else:
                aggregation = "month"
        
        # Get total conversations per time period
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_time, "$lte": end_time}
                }
            },
            {
                "$project": {
                    "time_bucket": {
                        "$dateTrunc": {
                            "date": "$created_at",
                            "unit": aggregation
                        }
                    },
                    "session_id": "$_id"
                }
            },
            {
                "$group": {
                    "_id": "$time_bucket",
                    "total_sessions": {"$sum": 1},
                    "session_ids": {"$addToSet": "$_id"}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        # Get handover events for the same time periods
        handover_pipeline = [
            {
                "$match": {
                    "event_type": EventType.CHAT_WORKFLOW_HANDOVER.value,
                    "created_at": {"$gte": start_time, "$lte": end_time},
                    "parent_id": {"$exists": True}
                }
            },
            {
                "$project": {
                    "time_bucket": {
                        "$dateTrunc": {
                            "date": "$created_at",
                            "unit": aggregation
                        }
                    },
                    "session_id": "$parent_id"
                }
            },
            {
                "$group": {
                    "_id": "$time_bucket",
                    "handover_sessions": {"$addToSet": "$session_id"}
                }
            }
        ]
        
        try:
            # Execute both pipelines in parallel
            with ThreadPoolExecutor() as executor:
                sessions_future = executor.submit(
                    lambda: list(ChatSession._get_collection().aggregate(pipeline))
                )
                handovers_future = executor.submit(
                    lambda: list(Event._get_collection().aggregate(handover_pipeline))
                )
                
                sessions_by_time = sessions_future.result()
                handovers_by_time = {
                    item["_id"]: set(str(sid) for sid in item["handover_sessions"])
                    for item in handovers_future.result()
                }
            
            # Process results
            data_points = []
            for period in sessions_by_time:
                time_bucket = period["_id"]
                total_sessions = period["total_sessions"]
                session_ids = set(str(id) for id in period.get("session_ids", []))
                handover_sessions = handovers_by_time.get(time_bucket, set())
                
                # Calculate containment rate
                contained_sessions = session_ids - handover_sessions
                containment_rate = (len(contained_sessions) / total_sessions * 100) if total_sessions > 0 else 0
                
                # Format time label based on aggregation
                if aggregation == "hour":
                    time_label = time_bucket.strftime("%Y-%m-%d %H:%M")
                elif aggregation == "day":
                    time_label = time_bucket.strftime("%Y-%m-%d")
                elif aggregation == "week":
                    # Show start of week (Monday)
                    time_label = f"Week of {time_bucket.strftime('%Y-%m-%d')}"
                else:  # month
                    time_label = time_bucket.strftime("%Y-%m")
                
                data_points.append({
                    "time": time_bucket.isoformat() + "Z",
                    "time_label": time_label,
                    "value": round(containment_rate, 2),
                    "unit": "percent"
                })
            
            return {
                "data": data_points,
                "metadata": {
                    "time_range": {
                        "start": start_time.isoformat() + "Z",
                        "end": end_time.isoformat() + "Z"
                    },
                    "aggregation": aggregation,
                    "total_data_points": len(data_points),
                    "max_data_points": 30
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating containment rate metrics: {str(e)}")
            raise

    @staticmethod
    def _get_sessions_by_hour(start_time: datetime, end_time: datetime) -> List[HourlySessionDataPoint]:
        """
        Get session counts grouped by hour of day (00-23), aggregated across all days.
        
        Args:
            start_time: Start datetime for the query
            end_time: End datetime for the query
            
        Returns:
            List of HourlySessionDataPoint objects for each hour of the day (00-23)
        """
        # Initialize counts for all 24 hours
        hour_counts = {f"{hour:02d}": 0 for hour in range(24)}
        
        # Get all sessions in the time period
        sessions = ChatSession.objects(
            created_at__gte=start_time,
            created_at__lte=end_time
        )
        
        # Count sessions by hour of creation
        for session in sessions:
            hour = session.created_at.hour
            hour_key = f"{hour:02d}"
            hour_counts[hour_key] += 1
        
        # Convert to list of data points
        result = [
            HourlySessionDataPoint(hour=hour, count=count)
            for hour, count in hour_counts.items()
        ]
        
        # Sort by hour
        result.sort(key=lambda x: x.hour)
        
        return result

    @staticmethod
    def get_bot_engagement_metrics(start_date: datetime, end_date: Optional[datetime] = None) -> BotEngagementMetricsData:
        """
        Calculate bot engagement metrics for the specified time range.
        
        Args:
            start_date: Start datetime (UTC) for the time range.
            end_date: End datetime (UTC) for the time range. If not provided, defaults to current time.
            
        Returns:
            BotEngagementMetricsData object with calculated metrics
        """
        start_time, end_time = AnalyticsService._get_time_range(start_date, end_date)
        
        # Get chat sessions in the time period
        chat_sessions = ChatSession.objects(
            created_at__gte=start_time,
            created_at__lte=end_time
        )
        
        total_sessions = chat_sessions.count()
        
        if total_sessions == 0:
            # Return empty metrics if no sessions found
            return BotEngagementMetricsData(
                avg_session_duration=0,
                avg_messages_per_session=0,
                avg_resolution_time=0,
                first_response_time=0,
                response_rate=0,
                first_response_time_distribution=[
                    DistributionDataPoint(range="0-5s", count=0),
                    DistributionDataPoint(range="6-15s", count=0),
                    DistributionDataPoint(range="16-30s", count=0),
                    DistributionDataPoint(range="31-60s", count=0),
                    DistributionDataPoint(range=">60s", count=0),
                ],
                session_duration_distribution=[
                    DistributionDataPoint(range="0-1m", count=0),
                    DistributionDataPoint(range="1-3m", count=0),
                    DistributionDataPoint(range="3-5m", count=0),
                    DistributionDataPoint(range="5-10m", count=0),
                    DistributionDataPoint(range=">10m", count=0),
                ],
                messages_per_session_distribution=[
                    MessageDistributionDataPoint(count="1-2", sessions=0),
                    MessageDistributionDataPoint(count="3-5", sessions=0),
                    MessageDistributionDataPoint(count="6-10", sessions=0),
                    MessageDistributionDataPoint(count="11-20", sessions=0),
                    MessageDistributionDataPoint(count=">20", sessions=0),
                ],
                last_updated=datetime.now(timezone.utc)
            )
        
        # Initialize metrics
        total_duration = 0
        total_messages = 0
        total_resolution_time = 0
        total_first_response_time = 0
        sessions_with_first_response = 0
        
        # Initialize distribution counters
        first_response_time_ranges = {
            "0-5s": 0,
            "6-15s": 0,
            "16-30s": 0,
            "31-60s": 0,
            ">60s": 0
        }
        
        session_duration_ranges = {
            "0-1m": 0,
            "1-3m": 0,
            "3-5m": 0,
            "5-10m": 0,
            ">10m": 0
        }
        
        messages_per_session_ranges = {
            "1-2": 0,
            "3-5": 0,
            "6-10": 0,
            "11-20": 0,
            ">20": 0
        }
        
        # Response rate tracking
        total_user_messages = 0
        total_bot_responses = 0
        
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
                    
                    # Track session duration distribution
                    if session_duration <= 60:  # 0-1m
                        session_duration_ranges["0-1m"] += 1
                    elif session_duration <= 180:  # 1-3m
                        session_duration_ranges["1-3m"] += 1
                    elif session_duration <= 300:  # 3-5m
                        session_duration_ranges["3-5m"] += 1
                    elif session_duration <= 600:  # 5-10m
                        session_duration_ranges["5-10m"] += 1
                    else:  # >10m
                        session_duration_ranges[">10m"] += 1
                
                # Count messages in this session
                total_messages += message_count
                
                # Track message count distribution
                if message_count <= 2:
                    messages_per_session_ranges["1-2"] += 1
                elif message_count <= 5:
                    messages_per_session_ranges["3-5"] += 1
                elif message_count <= 10:
                    messages_per_session_ranges["6-10"] += 1
                elif message_count <= 20:
                    messages_per_session_ranges["11-20"] += 1
                else:
                    messages_per_session_ranges[">20"] += 1
                
                # Find first user message and first bot response
                first_user_message = None
                first_bot_response = None
                
                for message in messages:
                    # Count user messages and bot responses for response rate
                    if message.sender_type == SenderType.USER.value:
                        total_user_messages += 1
                        if first_user_message is None:
                            first_user_message = message
                    elif message.sender_type == SenderType.ASSISTANT.value:
                        total_bot_responses += 1
                        if first_bot_response is None and first_user_message is not None:
                            first_bot_response = message
                
                # Calculate first response time
                if first_user_message and first_bot_response:
                    first_response_time = (first_bot_response.created_at - first_user_message.created_at).total_seconds()
                    total_first_response_time += first_response_time
                    sessions_with_first_response += 1
                    
                    # Track first response time distribution
                    if first_response_time <= 5:  # 0-5s
                        first_response_time_ranges["0-5s"] += 1
                    elif first_response_time <= 15:  # 6-15s
                        first_response_time_ranges["6-15s"] += 1
                    elif first_response_time <= 30:  # 16-30s
                        first_response_time_ranges["16-30s"] += 1
                    elif first_response_time <= 60:  # 31-60s
                        first_response_time_ranges["31-60s"] += 1
                    else:  # >60s
                        first_response_time_ranges[">60s"] += 1
        
        # Calculate averages
        avg_session_duration = int(total_duration / total_sessions) if total_sessions > 0 else 0
        avg_messages_per_session = round(total_messages / total_sessions, 1) if total_sessions > 0 else 0
        avg_resolution_time = int(total_resolution_time / total_sessions) if total_sessions > 0 else 0
        avg_first_response_time = int(total_first_response_time / sessions_with_first_response) if sessions_with_first_response > 0 else 0
        
        # Calculate response rate
        response_rate = round((total_bot_responses / total_user_messages * 100), 1) if total_user_messages > 0 else 0
        
        # Convert distribution dictionaries to lists of objects
        first_response_time_distribution = [
            DistributionDataPoint(range=range_label, count=count)
            for range_label, count in first_response_time_ranges.items()
        ]
        
        session_duration_distribution = [
            DistributionDataPoint(range=range_label, count=count)
            for range_label, count in session_duration_ranges.items()
        ]
        
        messages_per_session_distribution = [
            MessageDistributionDataPoint(count=range_label, sessions=sessions)
            for range_label, sessions in messages_per_session_ranges.items()
        ]
        
        return BotEngagementMetricsData(
            avg_session_duration=avg_session_duration,
            avg_messages_per_session=avg_messages_per_session,
            avg_resolution_time=avg_resolution_time,
            first_response_time=avg_first_response_time,
            response_rate=response_rate,
            first_response_time_distribution=first_response_time_distribution,
            session_duration_distribution=session_duration_distribution,
            messages_per_session_distribution=messages_per_session_distribution,
            last_updated=datetime.now(timezone.utc)
        )
