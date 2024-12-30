from app.models.mongodb.client import Client
from app.utils.logger import get_logger

from app.models.mongodb.client_structured_data_store import ClientStructuredDataStore
from app.models.mongodb.utils import CredentialManager
from app.models.schemas.database_config import PostgresConfig
from app.models.mongodb.enums import DatabaseType

from .base import BaseDataStoreService

logger = get_logger(__name__)


class PostgresService(BaseDataStoreService):
    """Service for managing PostgreSQL databases"""

    def __init__(self, admin_connection: dict, credential_manager: "CredentialManager"):
        super().__init__(admin_connection, credential_manager)
        import psycopg2

        self.driver = psycopg2

    def create_database(self, client: Client) -> "ClientStructuredDataStore":
        """Create a new PostgreSQL database for a client"""
        self._check_data_store_limit(client)

        try:
            db_name = f"client_{client.client_id.lower()}"
            username, password = self._generate_secure_credentials("pg_user")

            with self.driver.connect(**self.admin_connection) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute(f"CREATE USER {username} WITH PASSWORD '{password}'")
                    cur.execute(f"CREATE DATABASE {db_name} OWNER {username}")
                    cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {username}")

            config = PostgresConfig(
                database=db_name,
                username=username,
                password=password,
                host=self.admin_connection["host"],
                port=self.admin_connection.get("port", 5432),
                ssl_mode="prefer",
            )

            data_store = ClientStructuredDataStore(
                client=client,
                database_type=DatabaseType.POSTGRES,
                config=self.credential_manager.encrypt_config(config.dict()),
                is_active=True,
            )
            data_store.save()

            logger.info(f"Created PostgreSQL database for client: {client.client_id}")
            return data_store

        except Exception as e:
            logger.error(f"Error creating PostgreSQL database for client {client.client_id}", exc_info=True)
            raise

    def test_connection(self, config: dict) -> bool:
        try:
            with self.driver.connect(**config) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {str(e)}")
            return False
