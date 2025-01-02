from typing import Optional, List
from fastapi import HTTPException

from app.models.schemas.database_config import DatabaseConfig
from app.models.mongodb.client import Client
from app.models.mongodb.client_structured_data_store import ClientStructuredDataStore
from app.models.mongodb.utils import CredentialManager
from app.models.mongodb.enums import DatabaseType
from app.services.client.db_server import DBServerService
from app.utils.logger import get_logger

from .clickhouse import ClickHouseService
from .postgres import PostgresService
from .base import BaseDataStoreService


logger = get_logger(__name__)


class ClientStructuredDataStoreService:
    """Service for managing client database stores"""

    def __init__(self, credential_manager: "CredentialManager"):
        self.credential_manager = credential_manager
        self.db_server_service = DBServerService(credential_manager=credential_manager)

    def get_service(self, client_id: str, database_type: DatabaseType) -> BaseDataStoreService:
        """
        Get database service for a client with appropriate admin credentials
        fetched from the db server configuration
        """
        try:
            # Get admin connection from db server service
            admin_connection = self.db_server_service.get_client_db_server(
                client_id=client_id, database_type=database_type
            )

            # Create and return appropriate service
            if database_type == DatabaseType.CLICKHOUSE:
                return ClickHouseService(admin_connection, self.credential_manager)
            elif database_type == DatabaseType.POSTGRES:
                return PostgresService(admin_connection, self.credential_manager)

            raise ValueError(f"Unsupported database type: {database_type}")

        except Exception as e:
            logger.error(f"Error initializing database service for client {client_id}", exc_info=True)
            raise

    def create_client_database(self, client_id: str, database_type: DatabaseType) -> ClientStructuredDataStore:
        """Create a new database for a client"""
        try:
            client = Client.objects.get(client_id=client_id)
            service = self.get_service(client_id, database_type)
            return service.create_database(client)

        except Client.DoesNotExist:
            raise ValueError(f"Client not found: {client_id}")
        except Exception as e:
            logger.error(f"Error creating {database_type} database for client {client_id}", exc_info=True)
            raise

    def get_data_store(self, client_id: str, data_store_id: str) -> Optional[DatabaseConfig]:
        """Get decrypted database configuration for a client"""
        try:
            client = Client.objects.get(client_id=client_id)
            data_store = ClientStructuredDataStore.objects.get(client=client, id=data_store_id, is_active=True)
            return data_store

        except (Client.DoesNotExist, ClientStructuredDataStore.DoesNotExist):
            raise HTTPException(
                status_code=404, detail=f"No active database configuration found for client: {client_id}"
            )
        except Exception as e:
            logger.error(f"Error getting database config for client {client_id}", exc_info=True)
            raise

    def list_data_stores(self, client_id: str) -> List[DatabaseConfig]:
        """List all active database configurations for a client"""
        try:
            client = Client.objects.get(client_id=client_id)
            data_stores = ClientStructuredDataStore.objects(client=client)
            return data_stores
        except Client.DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Client not found for client: {client_id}")

    def deactivate_client_database(self, client_id: str, database_type: DatabaseType) -> None:
        """Deactivate a client's database"""
        try:
            client = Client.objects.get(client_id=client_id)
            data_store = ClientStructuredDataStore.objects.get(
                client=client, database_type=database_type, is_active=True
            )
            data_store.is_active = False
            data_store.save()

            logger.info(f"Deactivated {database_type} database for client: {client_id}")

        except Client.DoesNotExist:
            raise ValueError(f"Client not found: {client_id}")
        except ClientStructuredDataStore.DoesNotExist:
            logger.warning(f"No active {database_type} database found for client: {client_id}")
        except Exception as e:
            logger.error(f"Error deactivating database for client {client_id}", exc_info=True)
            raise
