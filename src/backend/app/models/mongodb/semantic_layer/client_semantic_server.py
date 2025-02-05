from mongoengine import fields
from app.models.mongodb.base import BaseDocument
from app.models.mongodb.client import Client
from app.models.mongodb.semantic_layer.config_models import SemanticLayerConfig
from app.models.mongodb.semantic_layer.config_models import SemanticEngineType


class ClientSemanticServer(BaseDocument):
    """Client-specific or global semantic layer server configuration"""

    server_name = fields.StringField(required=True, unique=True)
    engine_type = fields.StringField(required=True, choices=[t.value for t in SemanticEngineType])

    semantic_config = fields.EmbeddedDocumentField(SemanticLayerConfig, required=True)
    client = fields.ReferenceField(Client)
    is_active = fields.BooleanField(default=True)
    is_default = fields.BooleanField(default=False)
    metadata = fields.DictField(default={})

    meta = {
        "collection": "client_semantic_servers",
        "indexes": [
            "client",
            "created_at",
            ("client", "is_active"),
        ],
    }

    def clean(self):
        """Ensure only global servers can be marked as default"""
        super().clean()
        if self.client and self.is_default:
            raise ValueError("Client-specific servers cannot be marked as default")
