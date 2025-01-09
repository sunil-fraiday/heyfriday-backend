from typing import Optional
from app.models.mongodb.chat_message import ChatMessage
from app.models.mongodb.chat_message_suggestion import ChatMessageSuggestion
from app.services.client import ChannelRequestLogService, ClientChannelService
from app.schemas.chat import ChatMessageResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ChatMessageSuggestionService:
    @staticmethod
    def create_suggestion(message: ChatMessage) -> ChatMessageSuggestion:
        """Creates a suggestion based on the original message"""
        suggestion = ChatMessageSuggestion(
            chat_session=message.session,
            chat_message=message,
            text=message.text,
            attachments=message.attachments,
            data=message.data
        )
        suggestion.save()
        return suggestion

    @staticmethod
    def get_suggestions_for_session(chat_session_id: str, limit: int = 10) -> list[ChatMessageSuggestion]:
        """Retrieves recent suggestions for a chat session"""
        return ChatMessageSuggestion.objects(
            chat_session=chat_session_id
        ).order_by('-created_at').limit(limit)

    @staticmethod
    def get_suggestion(suggestion_id: str) -> Optional[ChatMessageSuggestion]:
        """Retrieves a specific suggestion by ID"""
        try:
            return ChatMessageSuggestion.objects.get(id=suggestion_id)
        except ChatMessageSuggestion.DoesNotExist:
            return None