from typing import Optional
from pydantic import BaseModel, Field


class ChatConfig(BaseModel):
    """Schema for chat configuration at the client level"""

    error_message: Optional[str] = Field(
        default="""
🤖 We're sorry!
We couldn't generate a response to your message.
Please try rephrasing your message and try again.
""",
        description="Custom error message to display when AI service fails",
    )
