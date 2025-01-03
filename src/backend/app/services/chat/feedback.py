from typing import List, Optional
from datetime import datetime, timezone

import mongoengine as me
from mongoengine import Q
from fastapi import HTTPException

from app.models.mongodb.chat_message import ChatMessage
from app.models.mongodb.chat_message_feedback import ChatMessageFeedback
from app.schemas.chat_message_feedback import ChatMessageFeedbackCreate, ChatMessageFeedbackResponse
from app.utils.logger import get_logger
from .message import get_id_filter

logger = get_logger(__name__)


class ChatMessageFeedbackService:
    @staticmethod
    def create_feedback(chat_message_id: str, feedback_data: ChatMessageFeedbackCreate) -> ChatMessageFeedbackResponse:
        """
        Create a new feedback for a chat message.
        """
        try:
            chat_message = ChatMessage.objects.get(**get_id_filter(chat_message_id))
        except me.DoesNotExist:
            raise HTTPException(status_code=404, detail="Chat message not found")

        feedback = ChatMessageFeedback(
            chat_message=chat_message,
            rating=feedback_data.rating,
            comment=feedback_data.comment,
            metadata=feedback_data.metadata,
        )
        feedback.save()

        logger.info(f"Created feedback for message {chat_message.id}")
        return ChatMessageFeedbackResponse.from_db_model(feedback)

    @staticmethod
    def update_feedback(
        feedback_id: str, rating: Optional[int] = None, comment: Optional[str] = None, metadata: Optional[dict] = None
    ) -> ChatMessageFeedbackResponse:
        """
        Update an existing feedback.
        """
        try:
            feedback = ChatMessageFeedback.objects.get(id=feedback_id)
        except me.DoesNotExist:
            raise HTTPException(status_code=404, detail="Feedback not found")

        if rating:
            feedback.rating = rating
        if comment is not None:
            feedback.comment = comment
        if metadata is not None:
            feedback.metadata = metadata

        feedback.updated_at = datetime.now(timezone.utc)
        feedback.save()

        logger.info(f"Updated feedback {feedback_id}")
        return ChatMessageFeedbackResponse.from_db_model(feedback)

    @staticmethod
    def get_message_feedback(message_id: str) -> List[ChatMessageFeedbackResponse]:
        """
        Get all feedback for a specific message.
        """
        try:
            chat_message = ChatMessage.objects.get(**get_id_filter(message_id))
        except me.DoesNotExist:
            raise HTTPException(status_code=404, detail="Chat message not found")

        feedback = ChatMessageFeedback.objects(chat_message=chat_message).order_by("-created_at")
        return [ChatMessageFeedbackResponse.from_db_model(f) for f in feedback]
