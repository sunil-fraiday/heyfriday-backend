from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.message import MessageResponse


class MessageProcessor:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_query(self, query_text: str) -> MessageResponse:
        try:
            result = await self.db.execute(query_text)
            data = result.mappings().all()
            return MessageResponse(message=str(data))
        except Exception as e:
            return MessageResponse(message=f"Error executing query: {str(e)}")
