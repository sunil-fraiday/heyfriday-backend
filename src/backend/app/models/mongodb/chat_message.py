from typing import List, Optional, Union
from enum import Enum
from datetime import datetime

from mongoengine import Document, EmbeddedDocument, fields

from app.models.mongodb.chat_session import ChatSession


class MessageCategory(str, Enum):
    MESSAGE = "message"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"


class Attachment(EmbeddedDocument):
    file_name = fields.StringField(required=True)
    file_type = fields.StringField(required=True)
    file_size = fields.IntField(required=True)
    file_url = fields.StringField(required=True)


class ChatMessage(Document):
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    sender = fields.StringField()
    sender_name = fields.StringField()
    session = fields.ReferenceField(ChatSession, required=True)
    text = fields.StringField(required=True)
    attachments = fields.EmbeddedDocumentListField(Attachment)
    sql_data = fields.DictField()
    category = fields.StringField(
        choices=[cat.value for cat in MessageCategory], default=MessageCategory.MESSAGE.value
    )
    edit = fields.BooleanField(default=False)

    meta = {"collection": "chat_messages", "indexes": ["created_at", "session", ("session", "created_at")]}