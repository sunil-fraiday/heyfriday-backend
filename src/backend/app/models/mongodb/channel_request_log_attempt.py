from mongoengine import fields, CASCADE
from enum import Enum

from .base import BaseDocument
from .utils import datetime_utc_now


class ChannelRequestLogAttemptStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class ChannelRequestLogAttempt(BaseDocument):
    channel_request_log = fields.ReferenceField("ChannelRequestLog", reverse_delete_rule=CASCADE)
    attempt_number = fields.IntField()
    response_status = fields.IntField(null=True)
    response_body = fields.DictField(null=True)
    error_message = fields.StringField(null=True)
    status = fields.StringField(choices=[c for c in ChannelRequestLogAttemptStatus])
    attempted_at = fields.DateTimeField(default=datetime_utc_now)

    meta = {
        "collection": "channel_request_log_attempts",
        "indexes": ["created_at", "channel_request_log", "attempted_at"],
    }
