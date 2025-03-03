from datetime import datetime
from mongoengine import EmbeddedDocument, EmbeddedDocumentListField
from mongoengine.fields import StringField, EmbeddedDocumentField

from .base import BaseDocument


class EntityIdentifier(EmbeddedDocument):
    """Entity identifier for associating charts with entities"""

    type = StringField(required=True)
    id = StringField(required=True)


class Identifiers(EmbeddedDocument):
    """Container for chart identifiers"""

    service_name = StringField(required=True)
    entities = EmbeddedDocumentListField(EntityIdentifier, default=[])


class Chart(BaseDocument):
    """Chart document model"""

    identifiers = EmbeddedDocumentField(Identifiers, required=True)
    chart_type = StringField(required=True)
    blob_name = StringField(required=True)
    presigned_url = StringField()

    title = StringField()
    description = StringField()

    meta = {
        "collection": "charts",
        "indexes": [
            "chart_type",
            "created_at",
            "identifiers.service_name",
            {"fields": ["identifiers.entities.type", "identifiers.entities.id"]},
        ],
    }
