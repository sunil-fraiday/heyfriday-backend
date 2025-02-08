from enum import Enum
from mongoengine import fields
from app.models.mongodb.base import BaseDocument

class RelationshipStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    FAILED = "failed"

class ClientSemanticLayerDataStore(BaseDocument):
    client_semantic_layer = fields.ReferenceField("ClientSemanticLayer", required=True)
    client_data_store = fields.ReferenceField("ClientDataStore", required=True)
    status = fields.StringField(
        choices=[status.value for status in RelationshipStatus],
        default=RelationshipStatus.PENDING.value
    )
    config = fields.DictField(default=dict)
    last_sync_at = fields.DateTimeField()
    error_message = fields.StringField()

    meta = {
        "collection": "client_semantic_layer_data_stores",
        "indexes": [
            "client_semantic_layer",
            "client_data_store",
            "created_at",
            ("client_semantic_layer", "client_data_store"),
            ("client_semantic_layer", "status"),
            ("client_semantic_layer", "last_sync_at")
        ]
    }

    def __str__(self):
        return f"DataStore {self.client_data_store.id} for SemanticLayer {self.client_semantic_layer.id}"