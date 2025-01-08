from mongoengine import fields

from app.models.mongodb.enums import DatabaseType, EngineType
from app.models.mongodb.utils import CredentialManager
from app.models.schemas.database_config import DatabaseConfig, ClickHouseConfig, PostgresConfig
from .enums import DatabaseType
from .base import BaseDocument


class ClientDataStore(BaseDocument):
    """MongoDB model for storing client database configurations"""

    client = fields.ReferenceField("Client", required=True)
    engine_type = fields.StringField(choices=[engine.value for engine in EngineType], required=True)
    database_type = fields.StringField(choices=[t.value for t in DatabaseType], required=True)
    config = fields.DictField(required=True)
    is_active = fields.BooleanField(default=True)

    meta = {
        "collection": "client_data_stores",
        "indexes": ["client", "database_type", ("client", "database_type"), "created_at"],
    }

    def get_config(self, credential_manager: CredentialManager) -> DatabaseConfig:
        """Get decrypted database configuration"""
        decrypted_config = credential_manager.decrypt_config(self.config)

        if self.database_type == DatabaseType.CLICKHOUSE.value:
            return ClickHouseConfig(**decrypted_config)
        elif self.database_type == DatabaseType.POSTGRES.value:
            return PostgresConfig(**decrypted_config)

        raise ValueError(f"Unsupported database type: {self.database_type}")
