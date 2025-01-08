from app.models.mongodb.chat_message import ChatMessage, SenderType, MessageCategory
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_system_chat_message(
    session, error_message: str, message_category: MessageCategory.INFO, confidence_score: float = 1.0
):
    system_message = ChatMessage(
        session=session,
        sender="System",
        sender_name="System",
        sender_type=SenderType.SYSTEM,
        text=error_message,
        category=message_category,
        confidence_score=confidence_score,
    )
    system_message.save()

    return system_message
