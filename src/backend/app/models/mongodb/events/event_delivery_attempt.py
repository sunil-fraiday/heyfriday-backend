from mongoengine import fields
from enum import Enum

from app.models.mongodb.base import BaseDocument
from app.models.mongodb.events.event_delivery import EventDelivery


class AttemptStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class EventDeliveryAttempt(BaseDocument):
    """
    Tracks individual delivery attempts.
    """

    event_delivery = fields.ReferenceField(EventDelivery, required=True)
    attempt_number = fields.IntField(required=True)

    status = fields.StringField(choices=[s.value for s in AttemptStatus], required=True)

    response_status = fields.IntField()
    response_body = fields.DictField()
    logs = fields.DictField()

    meta = {
        "collection": "event_delivery_attempts",
        "indexes": [
            "event_delivery",
            "attempt_number",
            ("event_delivery", "attempt_number"),
        ],
    }
