from app.models.mongodb.client import Client
from app.utils.logger import get_logger

from app.models.mongodb.client_data_store import ClientDataStore
from app.models.mongodb.utils import CredentialManager
from app.models.schemas.database_config import ClickHouseConfig
from app.models.mongodb.enums import DatabaseType

from .base import BaseDataStoreService

logger = get_logger(__name__)


class ClickHouseService(BaseDataStoreService):
    """Service for managing ClickHouse databases"""

    def __init__(self, admin_connection: dict, credential_manager: "CredentialManager"):
        super().__init__(admin_connection, credential_manager)
        import clickhouse_driver

        self.driver = clickhouse_driver

    def create_database(self, client: Client) -> "ClientDataStore":
        """Create a new ClickHouse database for a client"""
        self._check_data_store_limit(client)

        try:
            db_name = f"client_{client.client_id.lower()}"
            username, password = self._generate_secure_credentials("ch_user")

            with self.driver.Client(**self.admin_connection) as ch:
                ch.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
                ch.execute(f"CREATE USER IF NOT EXISTS {username} IDENTIFIED BY '{password}'")                
                ch.execute(f"GRANT SELECT ON {db_name}.* TO {username}")                

            config = ClickHouseConfig(
                database=db_name,
                user=username,
                password=password,
                host=self.admin_connection["host"],
                port=self.admin_connection.get("port", 9000),
                secure=True,
            )

            data_store = ClientDataStore(
                client=client,
                database_type=DatabaseType.CLICKHOUSE,
                config=self.credential_manager.encrypt_config(config.model_dump()),
                is_active=True,
            )
            data_store.save()

            logger.info(f"Created ClickHouse database for client: {client.client_id}")
            return data_store

        except Exception as e:
            logger.error(f"Error creating ClickHouse database for client {client.client_id}", exc_info=True)
            raise e

    def test_connection(self, config: dict) -> bool:
        try:
            with self.driver.Client(**config) as ch:
                ch.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"ClickHouse connection test failed: {str(e)}")
            return False
