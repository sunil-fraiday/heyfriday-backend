from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class ChatSessionResponse(BaseModel):
    """Schema for chat session response model"""
    id: str
    created_at: datetime
    updated_at: datetime
    active: bool
    client: Optional[str] = None
    client_channel: Optional[str] = None
    session_id: str
    participants: Optional[List[str]] = None


class ChatSessionListResponse(BaseModel):
    """Schema for list of chat sessions response"""
    sessions: List[ChatSessionResponse]
    total: int
