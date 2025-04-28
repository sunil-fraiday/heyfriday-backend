from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.mongodb.chat_message_feedback import ChatMessageFeedback


class ChatMessageFeedbackCreate(BaseModel):
    rating: int
    comment: Optional[str] = None
    metadata: Dict


class ChatMessageFeedbackResponse(BaseModel):
    id: str
    chat_message_id: str
    rating: int
    comment: Optional[str] = None
    metadata: Dict
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db_model(cls, feedback: ChatMessageFeedback) -> "ChatMessageFeedbackResponse":
        """Convert a database model instance to a response schema."""
        return cls(
            id=str(feedback.id),
            chat_message_id=str(feedback.chat_message.id),
            rating=feedback.rating,
            comment=feedback.comment,
            metadata=feedback.metadata,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
        )
