from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.models.mongodb.chat_message import MessageCategory, ChatMessage


class AttachmentCreate(BaseModel):
    file_name: str
    file_type: str
    file_size: int
    file_url: str


class ChatMessageCreate(BaseModel):
    sender: Optional[str] = None
    sender_name: Optional[str] = None
    session_id: Optional[str] = None
    text: str
    attachments: Optional[List[AttachmentCreate]] = None
    sql_data: Optional[dict] = None
    category: MessageCategory = MessageCategory.MESSAGE


class ChatMessageResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    sender: Optional[str]
    sender_name: Optional[str]
    session_id: str
    text: str
    attachments: Optional[List[AttachmentCreate]]
    category: MessageCategory
    edit: bool = False

    @classmethod
    def from_chat_message(cls, chat_message: ChatMessage):
        return cls(
            id=str(chat_message.id),
            created_at=chat_message.created_at,
            updated_at=chat_message.updated_at,
            sender=chat_message.sender,
            sender_name=chat_message.sender_name,
            session_id=str(chat_message.session.id),
            text=chat_message.text,
            attachments=(
                [AttachmentCreate(**a) for a in chat_message.attachments] if chat_message.attachments else None
            ),
            category=MessageCategory(chat_message.category),
            edit=chat_message.edit,
        )
