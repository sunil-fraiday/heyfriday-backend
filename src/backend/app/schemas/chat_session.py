from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field


class ChatSessionResponse(BaseModel):
    """Schema for chat session response model"""

    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.replace(tzinfo=timezone.utc).isoformat()})

    id: str
    created_at: datetime = Field(description="UTC timestamp with timezone info")
    updated_at: datetime = Field(description="UTC timestamp with timezone info")
    active: bool
    client: Optional[str] = None
    client_channel: Optional[str] = None
    session_id: str
    participants: Optional[List[str]] = None
    handover: bool = False


class ChatSessionListResponse(BaseModel):
    """Schema for list of chat sessions response"""

    sessions: List[ChatSessionResponse]
    total: int
