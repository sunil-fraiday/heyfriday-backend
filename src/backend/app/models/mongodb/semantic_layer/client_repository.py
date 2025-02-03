from enum import Enum
from mongoengine import fields
from app.models.mongodb.base import BaseDocument
from app.models.mongodb.client import Client

from app.models.mongodb.semantic_layer.config_models import RepositoryConfig


class ClientRepository(BaseDocument):
    """Repository configuration for storing semantic layer files"""

    repository_config = fields.EmbeddedDocumentField(RepositoryConfig, required=True)
    client = fields.ReferenceField(Client)  # Optional, None means it's a global default
    is_active = fields.BooleanField(default=True)
    is_default = fields.BooleanField(default=False)

    meta = {
        "collection": "client_repositories",
        "indexes": [
            "client",
            "created_at",
            ("client", "is_active"),
        ],
    }

    def clean(self):
        """Ensure only global repositories can be marked as default"""
        super().clean()
        if self.client and self.is_default:
            raise ValueError("Client-specific repositories cannot be marked as default")
