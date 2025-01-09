from mongoengine import fields
from app.models.mongodb.base import BaseDocument
from app.models.mongodb.chat_session import ChatSession
from app.models.mongodb.chat_message import ChatMessage, Attachment


class ChatMessageSuggestion(BaseDocument):
    chat_session = fields.ReferenceField(ChatSession, required=True)
    chat_message = fields.ReferenceField(ChatMessage, required=True)

    text = fields.StringField(required=True)
    attachments = fields.EmbeddedDocumentListField(Attachment)
    data = fields.DictField()

    meta = {
        "collection": "chat_message_suggestions",
        "indexes": ["created_at", "chat_session", "chat_message", ("chat_session", "created_at")],
    }

    def __str__(self):
        return f"Suggestion for message {self.chat_message.id}"
