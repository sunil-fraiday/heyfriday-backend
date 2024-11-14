from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.message import MessageRequest, MessageResponse
from app.services.message_processor import MessageProcessor

router = APIRouter()


@router.post("/process-message", response_model=MessageResponse)
async def process_message(request: MessageRequest, db: AsyncSession = Depends(get_db)):
    try:
        query_executor = MessageProcessor(db)
        response = await query_executor.execute_query(request.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
