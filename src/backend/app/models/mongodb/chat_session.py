from typing import List, Optional, Union
from enum import Enum
from datetime import datetime

import mongoengine as me
from mongoengine import Document, EmbeddedDocument, fields


class ChatSession(Document):
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    participants = fields.ListField(fields.StringField(), default=[])
    active = fields.BooleanField(default=True)

    meta = {"collection": "chat_sessions", "indexes": ["created_at", "updated_at"]}
