from enum import Enum
from mongoengine import fields, CASCADE

from app.models.mongodb.enums import ExecutionStatus
from .base import BaseDocument


class AnalysisType(str, Enum):
    CATEGORY = "category"
    INTENT = "intent"


class ChatMessageAnalysis(BaseDocument):
    chat_message = fields.ReferenceField("ChatMessage", required=True, reverse_delete_rule=CASCADE)

    analysis_type = fields.StringField(choices=[t.value for t in AnalysisType], required=True)
    analysis_data = fields.DictField()

    status = fields.StringField(
        choices=[status.value for status in ExecutionStatus], default=ExecutionStatus.COMPLETED
    )

    meta = {
        "collection": "chat_message_analyses",
        "indexes": [
            "chat_message",
            "analysis_type",
            ("chat_message", "analysis_type"),
            ("chat_message", "-created_at"),
            {"fields": ["processing_status"], "sparse": True},
        ],
    }

    def __str__(self):
        return f"Analysis({self.analysis_type}) for message {self.chat_message.id}"
