from enum import Enum
from mongoengine import fields
from app.models.mongodb.base import BaseDocument
from app.models.mongodb.semantic_layer.client_semantic_layer_data_store import ClientSemanticLayerDataStore


class SyncJobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class DataStoreSyncJob(BaseDocument):
    """Job for syncing data store schema with semantic layer"""

    client_semantic_layer_data_store = fields.ReferenceField(ClientSemanticLayerDataStore, required=True)
    status = fields.StringField(
        choices=[status.value for status in SyncJobStatus], default=SyncJobStatus.PENDING.value
    )
    logs = fields.ListField(fields.StringField())

    meta = {
        "collection": "data_store_sync_jobs",
        "indexes": [
            "client_semantic_layer_data_store",
            "created_at",
            "status",
            ("client_semantic_layer_data_store", "status"),
            ("client_semantic_layer_data_store", "-created_at"),
        ],
    }

   
    def add_log(self, message: str) -> None:
        """Add a log message with timestamp"""
        timestamp = self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        self.save()
