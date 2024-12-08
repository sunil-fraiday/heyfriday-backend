from mongoengine import fields
from enum import Enum

from .base import BaseDocument


class ChannelType(Enum):
    WEBHOOK = "webhook"
    SLACK = "slack"


class ClientChannel(BaseDocument):
    channel_type = fields.StringField(choices=[channel_type.value for channel_type in ChannelType], required=True)
    channel_config = fields.DictField(required=True)
    client = fields.ReferenceField("Client", required=True)
    is_active = fields.BooleanField(default=True)

    meta = {"collection": "client_channels", "indexes": ["created_at", "client"]}
