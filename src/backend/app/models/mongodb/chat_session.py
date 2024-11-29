from mongoengine import fields
from .base import BaseDocument


class ChatSession(BaseDocument):
    session_id = fields.StringField(required=False)
    active = fields.BooleanField(default=True)

    meta = {"collection": "chat_sessions", "indexes": ["created_at", "updated_at"]}
