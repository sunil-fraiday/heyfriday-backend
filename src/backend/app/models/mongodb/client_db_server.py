from mongoengine import fields
from app.models.mongodb.base import BaseDocument
from app.models.mongodb.client import Client

from app.models.mongodb.enums import DatabaseType, EngineType
from app.models.schemas.database_config import DatabaseConfig, ClickHouseConfig, PostgresConfig
from app.models.mongodb.utils import CredentialManager


class ClientDBServer(BaseDocument):
    """Model for storing database server configurations"""

    server_type = fields.StringField(choices=[t.value for t in DatabaseType], required=True)
    engine_type = fields.StringField(choices=[engine.value for engine in EngineType], required=True)
    config = fields.DictField(required=True)
    client = fields.ReferenceField(Client, required=False)
    is_default = fields.BooleanField(default=False)
    is_active = fields.BooleanField(default=True)

    meta = {
        "collection": "client_db_servers",
        "indexes": [
            "client",
            "server_type",
            "is_active",
            ("client", "server_type", "is_active"),
            ("server_type", "is_default", "is_active"),
        ],
    }
