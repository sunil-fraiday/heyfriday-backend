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
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Attachment(EmbeddedDocument):
    file_name = fields.StringField()
    file_type = fields.StringField()
    file_size = fields.IntField()
    file_url = fields.StringField()
    type = fields.StringField(default="image")  # "file", "image", "carousel"
    carousel = fields.DictField()


class ChatMessage(BaseDocument):
    external_id = fields.StringField(nullable=True)  # Id to identify the message from other systems
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
    config = fields.DictField()
    confidence_score = fields.FloatField(default=0.0)

    edit = fields.BooleanField(default=False)
    meta = {"collection": "chat_messages", "indexes": ["created_at", "session", ("session", "created_at")]}

    def is_suggestion_mode(self):
        return self.config and self.config.get("suggestion_mode", False)

    def get_message_config(self):
        from app.schemas.chat import MessageConfig

        return MessageConfig.model_validate(self.config)
