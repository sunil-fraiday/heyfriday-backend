from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.models.mongodb.chat_message import MessageCategory


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
