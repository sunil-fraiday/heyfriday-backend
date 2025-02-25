from mongoengine import fields, Q
from datetime import datetime, timezone
from typing import List, Optional, Dict

from app.models.mongodb.base import BaseDocument
from .event_types import EventType, EntityType


class Event(BaseDocument):
    """
    Event model for storing system events with parent-child relationships.
    """

    event_type = fields.StringField(choices=[e.value for e in EventType], required=True)
    entity_type = fields.StringField(choices=[e.value for e in EntityType], required=True)
    entity_id = fields.StringField(required=True)
    parent_id = fields.StringField(required=False)
    data = fields.DictField(default=dict)

    meta = {
        "collection": "events",
        "indexes": [
            "event_type",
            "entity_type",
            "entity_id",
            "parent_id",
            ("entity_type", "entity_id"),
            ("parent_id", "event_type"),
            ("event_type", "created_at"),
        ],
    }
