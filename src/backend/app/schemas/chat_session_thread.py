from typing import List
from datetime import datetime
from pydantic import BaseModel, Field


class ThreadConfig(BaseModel):
    """Schema for thread configuration at the client level"""
    enabled: bool = True
    inactivity_minutes: int = 1440  # Minutes before a thread is considered inactive (default: 24 hours)


class ThreadResponse(BaseModel):
    """Schema for thread response"""
    thread_id: str
    thread_session_id: str
    parent_session_id: str
    chat_session_id: str
    active: bool
    last_activity: datetime = Field(description="UTC timestamp of last activity")


class ThreadListResponse(BaseModel):
    """Schema for list of threads response"""
    threads: List[ThreadResponse]
    total: int
