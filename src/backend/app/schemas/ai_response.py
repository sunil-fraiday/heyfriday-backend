from pydantic import BaseModel, Field
from datetime import datetime
from app.models.mongodb.chat_message import SenderType

from typing import List, Union, Dict
from .chat import ChatMessageResponse


class Answer(BaseModel):
    answer_text: str
    answer_data: Union[List[Dict], Dict]
    answer_url: str


class Data(BaseModel):
    answer: Answer


class AIResponse(BaseModel):
    status: str
    message: str
    data: Data


class AIServiceRequest(BaseModel):
    current_message: str
    chat_history: List[ChatMessageResponse] = Field(default_factory=list)
    session_id: str
    sender_id: str
    created_at: datetime
    updated_at: datetime
    sender_type: SenderType
    current_message_id: str
