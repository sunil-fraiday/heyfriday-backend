from enum import Enum
from mongoengine import fields
from app.models.mongodb.base import BaseDocument
from app.models.mongodb.client_data_store import ClientDataStore
from app.models.mongodb.semantic_layer.client_semantic_layer import ClientSemanticLayer


class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class DataStoreSyncJob(BaseDocument):
    """Job for syncing data store schema with semantic layer"""

    client_semantic_layer = fields.ReferenceField(ClientSemanticLayer, required=True)
    client_data_store = fields.ReferenceField(ClientDataStore, required=True)
    status = fields.StringField(choices=[status.value for status in JobStatus], default=JobStatus.PENDING.value)
    logs = fields.ListField(fields.StringField())

    meta = {
        "collection": "data_store_sync_jobs",
        "indexes": [
            "semantic_layer",
            "data_store",
            "created_at",
            "status",
            ("semantic_layer", "data_store", "status"),
            ("semantic_layer", "data_store", "-created_at"),
        ],
    }

    def add_log(self, message: str) -> None:
        """Add a log message with timestamp"""
        timestamp = self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        self.save()
