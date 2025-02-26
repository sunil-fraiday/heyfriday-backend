from mongoengine import fields
from enum import Enum

from app.models.mongodb.base import BaseDocument
from app.models.mongodb.events.event import Event
from app.models.mongodb.events.event_processor_config import EventProcessorConfig


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class EventDelivery(BaseDocument):
    """
    Tracks the delivery of an event to a specific processor.
    """
    event = fields.ReferenceField(Event, required=True)
    event_processor_config = fields.ReferenceField(EventProcessorConfig, required=True)
    
    status = fields.StringField(choices=[s.value for s in DeliveryStatus], default=DeliveryStatus.PENDING.value)
    max_attempts = fields.IntField(default=3)
    current_attempts = fields.IntField(default=0)
    
    request_payload = fields.DictField()
    
    meta = {
        "collection": "event_deliveries",
        "indexes": [
            "event",
            "event_processor_config",
            "status",
            ("event", "event_processor_config"),
            ("status", "created_at"),
        ]
    }