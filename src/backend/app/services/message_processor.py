import re
from typing import Dict, List
from sqlalchemy.orm import Session

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

    def _format_response(self, query_type: str, data: List[Dict]) -> str:
        if not data:
            return "No data found for the specified period."

        if query_type == "sessions":
            total_sessions = sum(row["total_sessions"] for row in data)
            return f"Total sessions in the last 7 days: {total_sessions:,.0f}\n\nDaily breakdown:\n" + "\n".join(
                f"{row['ga_date']}: {row['total_sessions']:,.0f} sessions" for row in data
            )

        elif query_type == "users":
            total_users = sum(row["total_users"] for row in data)
            active_users = sum(row["active_users"] for row in data)
            return (
                f"Total users in the last 7 days: {total_users:,.0f}\nActive users: {active_users:,.0f}\n\nDaily breakdown:\n"
                + "\n".join(
                    f"{row['ga_date']}: {row['total_users']:,.0f} total, {row['active_users']:,.0f} active"
                    for row in data
                )
            )

        elif query_type == "sessions_per_user":
            avg_spu = sum(row["avg_sessions_per_user"] for row in data) / len(data)
            return f"Average sessions per user in the last 7 days: {avg_spu:.2f}\n\nDaily breakdown:\n" + "\n".join(
                f"{row['ga_date']}: {row['avg_sessions_per_user']:.2f} sessions/user" for row in data
            )

        elif query_type == "channel_breakdown":
            return "Channel Distribution:\n\n" + "\n".join(
                f"{row['defaultChannelGroup']}:\n"
                + f"  Sessions: {row['total_sessions']:,.0f}\n"
                + f"  Users: {row['total_users']:,.0f}\n"
                + f"  Avg Sessions/User: {row['avg_sessions_per_user']:.2f}"
                for row in data
            )

        return str(data)

    async def execute_query(self, message: str) -> MessageResponse:
        try:
            query_type = None
            query_func = None

            # Find matching query pattern
            for pattern, func in self.query_patterns.items():
                if re.search(pattern, message.lower()):
                    query_func = func
                    query_type = pattern.split("|")[0].strip("()")
                    break

            if not query_func:
                return MessageResponse(
                    message="I couldn't understand what analytics you're looking for. Try asking about sessions, users, sessions per user, or channel breakdown."
                )

            # Execute query
            query = query_func()
            result = await self.db.execute(query)
            data = [dict(row) for row in result.mappings().all()]

            # Format response
            response_message = self._format_response(query_type, data)

            return MessageResponse(message=response_message, data=data)

        except Exception as e:
            return MessageResponse(message=f"Error executing query: {str(e)}", data=None)
