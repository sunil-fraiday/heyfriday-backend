import re
import traceback
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.message import MessageResponse


class MessageProcessor:
    def __init__(self, db: Session):
        self.db = db
        self.query_patterns = {
            r"(number|count|how many) sessions": self._get_sessions_query,
            r"(number|count|how many) users": self._get_users_query,
            r"sessions per user": self._get_sessions_per_user_query,
            r"channel (breakdown|distribution|split)": self._get_channel_breakdown_query,
            r"(top|best) performing channels": self._get_top_channels_query,
            r"engagement rate": self._get_engagement_query,
        }

    def _get_sessions_query(self) -> str:
        return """
        SELECT 
            ga_date,
            SUM(sessions) as total_sessions
        FROM sample_ga_session_data
        WHERE ga_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY ga_date
        ORDER BY ga_date DESC;
        """

    def _get_users_query(self) -> str:
        return """
        SELECT 
            ga_date,
            SUM(totalUsers) as total_users,
            SUM(activeUsers) as active_users
        FROM sample_ga_session_data
        WHERE ga_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY ga_date
        ORDER BY ga_date DESC;
        """

    def _get_sessions_per_user_query(self) -> str:
        return """
        SELECT 
            ga_date,
            AVG(sessionsPerUser) as avg_sessions_per_user
        FROM sample_ga_session_data
        WHERE ga_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY ga_date
        ORDER BY ga_date DESC;
        """

    def _get_channel_breakdown_query(self) -> str:
        return """
        SELECT 
            defaultChannelGroup,
            COUNT(*) as count,
            SUM(sessions) as total_sessions,
            SUM(totalUsers) as total_users,
            AVG(sessionsPerUser) as avg_sessions_per_user
        FROM sample_ga_session_data
        WHERE ga_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY defaultChannelGroup
        ORDER BY total_sessions DESC;
        """

    def _get_top_channels_query(self) -> str:
        return """
        SELECT 
            defaultChannelGroup,
            SUM(sessions) as total_sessions,
            SUM(engagedSessions) as engaged_sessions,
            SUM(totalUsers) as total_users,
            AVG(cartToViewRate) as avg_cart_to_view_rate
        FROM sample_ga_session_data
        WHERE ga_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY defaultChannelGroup
        ORDER BY total_sessions DESC
        LIMIT 5;
        """

    def _get_engagement_query(self) -> str:
        return """
        SELECT 
            ga_date,
            SUM(engagedSessions) / NULLIF(SUM(sessions), 0) * 100 as engagement_rate
        FROM sample_ga_session_data
        WHERE ga_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY ga_date
        ORDER BY ga_date DESC;
        """

    async def execute_query(self, message: str) -> MessageResponse:
        try:
            query_func = None

            # Find matching query pattern
            for pattern, func in self.query_patterns.items():
                if re.search(pattern, message.lower()):
                    query_func = func
                    break

            if not query_func:
                return MessageResponse(
                    message="I couldn't understand what analytics you're looking for. Try asking about sessions, users, sessions per user, or channel breakdown."
                )

            # Execute query
            query = query_func()
            result = self.db.execute(text(query))
            data = [dict(row) for row in result.mappings().all()]

            return MessageResponse(message = "Here is the result for your question", sql_data=data)

        except Exception as e:
            logging.error(str(e) + traceback.format_exc())
            return MessageResponse(message=f"Error executing query: {str(e)}", data=None)
