from typing import List
from fastapi import APIRouter, HTTPException, Path

from app.schemas.chat_message_feedback import (
    ChatMessageFeedbackCreate,
    ChatMessageFeedbackResponse,
)
from app.services.chat.feedback import ChatMessageFeedbackService
from app.utils.logger import get_logger


router = APIRouter(prefix="/messages/{message_id}/feedbacks", tags=["feedback"])

logger = get_logger(__name__)


@router.post(
    "",
    response_model=ChatMessageFeedbackResponse,
    status_code=201,
)
def create_feedback(
    message_id: str,
    feedback_data: ChatMessageFeedbackCreate,
) -> ChatMessageFeedbackResponse:
    try:
        feedback = ChatMessageFeedbackService.create_feedback(message_id, feedback_data)
        return feedback
    except Exception as e:
        logger.error(f"Error creating feedback: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Error creating feedback")


@router.get(
    "",
    response_model=List[ChatMessageFeedbackResponse],
)
async def get_message_feedback(
    message_id: str = Path(..., description="The ID of the chat message"),
) -> List[ChatMessageFeedbackResponse]:
    return ChatMessageFeedbackService.get_message_feedback(message_id)


@router.patch(
    "/{feedback_id}",
    response_model=ChatMessageFeedbackResponse,
)
async def update_feedback(
    feedback_id: str = Path(..., description="The ID of the feedback to update"),
    rating: int | None = None,
    comment: str | None = None,
    metadata: dict | None = None,
) -> ChatMessageFeedbackResponse:
    return ChatMessageFeedbackService.update_feedback(
        feedback_id=feedback_id,
        rating=rating,
        comment=comment,
        metadata=metadata,
    )
