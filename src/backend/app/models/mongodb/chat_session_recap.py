from mongoengine import fields
from enum import Enum

from app.models.mongodb.base import BaseDocument
from app.models.mongodb.enums import ExecutionStatus


class ChatSessionRecap(BaseDocument):
    chat_session = fields.ReferenceField("ChatSession", required=True)
    chat_messages = fields.ListField(fields.ReferenceField("ChatMessage"), required=True)

    recap_data = fields.DictField(nulllable=True)

    status = fields.StringField(
        choices=[status.value for status in ExecutionStatus], default=ExecutionStatus.COMPLETED
    )
    error_message = fields.StringField()

    meta = {
        "collection": "chat_session_recaps",
        "indexes": [
            "chat_session",
            "created_at",
            ("chat_session", "-created_at"),
            {"fields": ["chat_messages"], "sparse": True},
        ],
    }

    def __str__(self):
        return f"Recap for session {self.chat_session.id} ({len(self.chat_messages)} messages)"
