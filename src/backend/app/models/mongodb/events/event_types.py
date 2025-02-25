from enum import Enum


class EventType(str, Enum):
    # Chat Session Events
    CHAT_SESSION_CREATED = "chat_session_created"
    CHAT_SESSION_INACTIVE = "chat_session_inactive"

    # Chat Message Events
    CHAT_MESSAGE_CREATED = "chat_message_created"
    CHAT_MESSAGE_PROCESSING = "chat_message_processing"
    CHAT_MESSAGE_COMPLETED = "chat_message_completed"
    CHAT_MESSAGE_ERROR = "chat_message_error"
    CHAT_MESSAGE_HANDOVER = "chat_message_handover"

    # AI Service Events
    AI_REQUEST_SENT = "ai_request_sent"
    AI_RESPONSE_RECEIVED = "ai_response_received"


class EntityType(str, Enum):
    CHAT_SESSION = "chat_session"
    CHAT_MESSAGE = "chat_message"
    AI_SERVICE = "ai_service"
