from enum import Enum

from mongoengine import EmbeddedDocument, fields

from app.models.mongodb.chat_session import ChatSession
from .base import BaseDocument


class MessageCategory(str, Enum):
    MESSAGE = "message"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"


class SenderType(str, Enum):
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"


class Attachment(EmbeddedDocument):
    file_name = fields.StringField(required=True)
    file_type = fields.StringField(required=True)
    file_size = fields.IntField(required=True)
    file_url = fields.StringField(required=True)


class ChatMessage(BaseDocument):
    sender = fields.StringField()
    sender_name = fields.StringField()
    sender_type = fields.StringField(
        choices=[sender_type.value for sender_type in SenderType], default=SenderType.USER
    )
    session = fields.ReferenceField(ChatSession, required=True)
    text = fields.StringField(required=True)
    attachments = fields.EmbeddedDocumentListField(Attachment)
    data = fields.DictField()
    category = fields.StringField(
        choices=[cat.value for cat in MessageCategory], default=MessageCategory.MESSAGE.value
    )

    edit = fields.BooleanField(default=False)
    meta = {"collection": "chat_messages", "indexes": ["created_at", "session", ("session", "created_at")]}
