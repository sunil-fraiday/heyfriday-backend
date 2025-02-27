from enum import Enum


class EventType(str, Enum):
    # Chat Session Events
    CHAT_SESSION_CREATED = "chat_session_created"
    CHAT_SESSION_INACTIVE = "chat_session_inactive"

    # Chat Message Events
    CHAT_MESSAGE_CREATED = "chat_message_created"

    # Chat Workflow Events
    CHAT_WORKFLOW_PROCESSING = "chat_workflow_processing"
    CHAT_WORKFLOW_COMPLETED = "chat_workflow_completed"
    CHAT_WORKFLOW_ERROR = "chat_workflow_error"
    CHAT_WORKFLOW_HANDOVER = "chat_workflow_handover"

    # Chat Message Suggestion Events 
    CHAT_SUGGESTION_CREATED = "chat_suggestion_created"
    
    # AI Service Events
    AI_REQUEST_SENT = "ai_request_sent"
    AI_RESPONSE_RECEIVED = "ai_response_received"


class EntityType(str, Enum):
    CHAT_SESSION = "chat_session"
    CHAT_MESSAGE = "chat_message"
    CHAT_SUGGESTION = "chat_suggestion"
    AI_SERVICE = "ai_service"
