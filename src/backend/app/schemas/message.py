from pydantic import BaseModel
from typing import Optional


class MessageRequest(BaseModel):
    message: str
    user: str
    channel: str
    thread_ts: Optional[str] = None
    thread_context: Optional[str] = None


class MessageResponse(BaseModel):
    message: str
    image_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Here's the analysis you requested...",
                "image_url": "https://example.com/image.png",
            }
        }
