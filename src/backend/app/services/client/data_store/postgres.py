from typing import Dict, List, Any

from app.models.mongodb.client import Client
from app.utils.logger import get_logger

from app.models.mongodb.client_data_store import ClientDataStore
from app.models.mongodb.utils import CredentialManager
from app.models.schemas.database_config import PostgresConfig
from app.models.mongodb.enums import DatabaseType, EngineType

from .base import BaseDataStoreService

logger = get_logger(__name__)


class PostgresService(BaseDataStoreService):
    """Service for managing PostgreSQL databases"""

    ENGINE_TYPE = EngineType.STRUCTURED

    def __init__(self, admin_connection: dict, credential_manager: "CredentialManager"):
        super().__init__(admin_connection, credential_manager)
        import psycopg2

        self.driver = psycopg2

    def create_database(self, client: Client) -> "ClientDataStore":
        """Create a new PostgreSQL database for a client"""
        self._check_data_store_limit(client, self.ENGINE_TYPE)

        try:
            db_name = f"client_{client.client_id.lower()}"
            username, password = self._generate_secure_credentials(f"user")

            conn = self.driver.connect(
                **self.admin_connection
            )  # default admin db from the db server would be used here
            conn.autocommit = True
            try:
                with conn.cursor() as cur:
                    # Check if user exists before creating
                    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (username,))
                    if not cur.fetchone():
                        cur.execute(f"CREATE USER {username} WITH PASSWORD '{password}'")

                    # Check if database exists before creating
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                    if not cur.fetchone():
                        cur.execute(f"CREATE DATABASE {db_name} OWNER {self.admin_connection['user']}")
            finally:
                conn.close()

            # Connect to the new database to set up permissions
            db_conn = self.driver.connect(**{**self.admin_connection, "database": db_name})
            db_conn.autocommit = True
            try:
                with db_conn.cursor() as cur:
                    # Set up read-only permissions for regular user
                    cur.execute(
                        f"""
                        DO $$
                        BEGIN
                            EXECUTE format('GRANT CONNECT ON DATABASE {db_name} TO {username}');
                            GRANT USAGE ON SCHEMA public TO {username};
                            GRANT SELECT ON ALL TABLES IN SCHEMA public TO {username};
                            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {username};
                        EXCEPTION 
                            WHEN duplicate_object THEN NULL;
                        END $$;
                    """
                    )
            finally:
                db_conn.close()

            config = PostgresConfig(
                database=db_name,
                user=username,
                password=password,
                host=self.admin_connection["host"],
                port=self.admin_connection.get("port", 5432),
                ssl_mode="prefer",
            )

            data_store = ClientDataStore(
                client=client,
                database_type=DatabaseType.POSTGRES,
                engine_type=self.ENGINE_TYPE.value,
                config=self.credential_manager.encrypt_config(config.dict()),
                is_active=True,
            )
            data_store.save()

            logger.info(f"Created PostgreSQL database for client: {client.client_id}")
            return data_store

        except Exception as e:
            logger.error(f"Error creating PostgreSQL database for client {client.client_id}", exc_info=True)
            raise

    def raw_execute(self, config: Dict[str, Any], query: str, params: Dict = None) -> List[tuple]:
        """Execute raw query on PostgreSQL"""
        try:
            with self.driver.connect(**config) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params or {})
                    return cur.fetchall() if cur.description else []

        except Exception as e:
            logger.error("Error executing raw PostgreSQL query", exc_info=True)
            raise ValueError(f"Database query error: {str(e)}")

    def test_connection(self, config: dict) -> bool:
        try:
            with self.driver.connect(**config) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {str(e)}")
            return False
