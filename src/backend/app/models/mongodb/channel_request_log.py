from mongoengine import fields
from enum import Enum

from .base import BaseDocument


class ChannelRequestLogStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"


class EntityType(str, Enum):
    CHAT_MESSAGE = "chat_message"
    CHAT_SUGGESTION = "chat_suggestion"


class ChannelRequestLog(BaseDocument):
    entity_type = fields.StringField(choices=[e.value for e in EntityType], default=EntityType.CHAT_MESSAGE.value)
    entity_id = fields.StringField(required=True)
    chat_message = fields.ReferenceField("ChatMessage", required=True)
    client_channel = fields.ReferenceField("ClientChannel", required=True)
    request_payload = fields.DictField(nullable=True)
    request_headers = fields.DictField(nullable=True)
    max_attempts = fields.IntField(default=3)
    status = fields.StringField(
        choices=[s.value for s in ChannelRequestLogStatus], default=ChannelRequestLogStatus.PENDING.value
    )

    meta = {
        "collection": "channel_request_logs",
        "indexes": [
            "created_at",
            "updated_at",
            "chat_message",
            "client_channel",
            "entity_id",
            "entity_type",
        ],
    }
