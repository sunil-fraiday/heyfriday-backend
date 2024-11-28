from mongoengine import Document, fields
from .utils import datetime_utc_now


class ChatSession(Document):
    session_id = fields.StringField(required=False)
    created_at = fields.DateTimeField(default=datetime_utc_now)
    updated_at = fields.DateTimeField(default=datetime_utc_now)
    participants = fields.ListField(fields.StringField(), default=[])
    active = fields.BooleanField(default=True)

    meta = {"collection": "chat_sessions", "indexes": ["created_at", "updated_at"]}
