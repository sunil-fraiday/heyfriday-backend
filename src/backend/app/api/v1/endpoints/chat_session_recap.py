from fastapi import APIRouter, HTTPException, Depends

from app.services.chat.message import ChatMessageService
from app.services.chat.recap import ChatRecapService
from app.schemas.chat_session_recap import ChatSessionRecapResponse
from app.models.mongodb.chat_session_recap import ExecutionStatus
from app.models.mongodb.chat_session import ChatSession
from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="", tags=["Chat Sessions Recap"])


@router.post("/sessions/{session_id}/recap", response_model=ChatSessionRecapResponse)
def generate_session_recap(
    session_id: str,
):
    """
    Generate a recap for the specified chat session.
    """
    try:
        session = ChatSession.objects.get(session_id=session_id)
        messages = ChatMessageService.list_messages(session_id=session_id)

        if not messages:
            raise HTTPException(status_code=404, detail="No messages found for recap generation")

        recap = ChatRecapService(
            aws_runtime=settings.AWS_BEDROCK_RUNTIME,
            region_name=settings.AWS_BEDROCK_REGION,
            access_key_id=settings.AWS_BEDROCK_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_BEDROCK_SECRET_ACCESS_KEY,
            model_name="mistral.mistral-large-2402-v1:0",
        ).generate_recap(chat_session=session, messages=messages)

        if recap.status == ExecutionStatus.FAILED:
            raise HTTPException(status_code=400, detail=f"Failed to generate recap. Please try again.")

        return ChatSessionRecapResponse(session_id=session_id, **recap.to_serializable_dict())
    except ChatSession.DoesNotExist:
        raise HTTPException(status_code=404, detail="Chat session not found")
    except Exception as e:
        logger.error(f"Error generating recap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating recap. Please try again")


@router.get("/sessions/{session_id}/recap", response_model=ChatSessionRecapResponse)
def get_session_recap(session_id: str):
    """
    Get the latest recap for the specified chat session.
    """
    try:
        session = ChatSession.objects.get(session_id=session_id)
        recap = ChatRecapService.get_latest_recap(session)

        if not recap:
            raise HTTPException(status_code=404, detail="No recap found for this session")

        return ChatSessionRecapResponse(session_id=session_id, **recap.to_serializable_dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving recap: {str(e)}")
