from mongoengine import fields
from app.models.mongodb.base import BaseDocument
from app.models.mongodb.client import Client
from app.models.mongodb.client_data_store import ClientDataStore
from app.models.mongodb.semantic_layer.client_repository import ClientRepository
from app.models.mongodb.semantic_layer.client_semantic_server import ClientSemanticServer
from app.models.mongodb.semantic_layer.config_models import SemanticLayerConfig


class ClientSemanticLayer(BaseDocument):
    """Client-specific semantic layer configuration"""

    client = fields.ReferenceField(Client, required=True)
    client_repository = fields.ReferenceField(ClientRepository)
    client_semantic_server = fields.ReferenceField(ClientSemanticServer)
    client_data_stores = fields.ListField(fields.ReferenceField(ClientDataStore))
    repository_folder = fields.StringField()
    is_active = fields.BooleanField(default=True)

    meta = {
        "collection": "client_semantic_layers",
        "indexes": [
            "client",
            "client_repository",
            "client_semantic_server",
            "client_data_stores",
            "created_at",
        ],
    }

    def clean(self):
        """Validate configuration based on semantic layer setup"""
        super().clean()
        if not self.repository_folder:
            self.repository_folder = str(self.client.id)
