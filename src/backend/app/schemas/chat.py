from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.mongodb.chat_message import MessageCategory, ChatMessage


class MessageConfig(BaseModel):
    suggestion_mode: bool = Field(default=False, description="Whether to create suggestions instead of messages")
    ai_enabled: bool = Field(default=True, description="Whether to enable AI processing")


class AttachmentCreate(BaseModel):
    file_name: str
    file_type: str
    file_size: int
    file_url: str


class BaseChatMessageCreate(BaseModel):
    sender: Optional[str] = None
    sender_name: Optional[str] = None
    created_at: Optional[str] = None
    text: str
    attachments: Optional[List[AttachmentCreate]] = None
    data: Optional[dict] = None
    category: MessageCategory = MessageCategory.MESSAGE


class ChatMessageCreate(BaseChatMessageCreate):
    client_id: str = None
    client_channel_type: str = None
    session_id: str = None
    config: Optional[dict] = Field(default_factory=MessageConfig)
    external_id: Optional[str] = None


class BulkChatMessageCreate(BaseModel):
    messages: List[BaseChatMessageCreate]
    session_id: str
    client_id: str = None
    client_channel_type: str = None


class ChatMessageResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    sender_id: Optional[str]
    sender_name: Optional[str]
    sender_type: Optional[str]
    session_id: str
    text: str
    data: Optional[dict] = Field(default_factory=dict)
    attachments: Optional[List[AttachmentCreate]]
    category: MessageCategory
    confidence_score: float
    edit: bool = False

    @classmethod
    def from_chat_message(cls, chat_message: ChatMessage):
        return cls(
            id=str(chat_message.id),
            created_at=chat_message.created_at,
            updated_at=chat_message.updated_at,
            sender_id=chat_message.sender,
            sender_name=chat_message.sender_name,
            session_id=str(chat_message.session.session_id),
            text=chat_message.text,
            data=chat_message.data,
            attachments=(
                [AttachmentCreate(**a.to_mongo().to_dict()) for a in chat_message.attachments]
                if chat_message.attachments
                else None
            ),
            category=MessageCategory(chat_message.category),
            sender_type=chat_message.sender_type,
            edit=chat_message.edit,
            confidence_score=chat_message.confidence_score,
        )
