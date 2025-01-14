import secrets
from typing import Dict
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.models.mongodb.client import Client
from app.models.mongodb.client_data_store import ClientDataStore
from app.models.mongodb.enums import DatabaseType, EngineType
from app.models.mongodb.utils import CredentialManager
from app.models.schemas.database_config import QdrantConfig
from app.utils.logger import get_logger
from .base import BaseDataStoreService

logger = get_logger(__name__)


class QdrantService(BaseDataStoreService):
    """Service for managing Qdrant vector databases"""

    def __init__(self, admin_connection: QdrantConfig, credential_manager: "CredentialManager"):
        """
        Initialize with admin connection details and credential manager
        admin_connection should contain api_key for the Qdrant instance
        """
        super().__init__(admin_connection, credential_manager)
        self.client = QdrantClient(
            url=admin_connection.url,
            api_key=admin_connection.api_key,
            timeout=admin_connection.timeout,
            https=admin_connection.https,
        )

    def create_database(self, client: Client) -> ClientDataStore:
        """Create a new Qdrant collection for a client"""
        try:
            collection_name = f"client_{client.client_id.lower()}_{secrets.token_hex(4)}"

            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )

            config = QdrantConfig(
                url=self.admin_connection.get("url"),
                collection_name=collection_name,
                api_key=self.admin_connection.get("api_key"),
                https=self.admin_connection.get("https"),
                timeout=10.0,
            )

            encrypted_config = self.credential_manager.encrypt_config(config)

            data_store = ClientDataStore(
                client=client,
                database_type=DatabaseType.QDRANT.value,
                engine_type=EngineType.UNSTRUCTURED.value,
                config=encrypted_config,
                is_active=True,
            )
            data_store.save()

            logger.info(f"Created Qdrant collection for client: {client.client_id}")
            return data_store

        except Exception as e:
            logger.error(f"Error creating Qdrant collection for client {client.client_id}", exc_info=True)
            self._cleanup_failed_creation(collection_name)
            raise ValueError(f"Failed to create Qdrant collection: {str(e)}")

    def _cleanup_failed_creation(self, collection_name: str) -> None:
        """Cleanup collection if creation fails"""
        try:
            self.client.delete_collection(collection_name=collection_name)
        except Exception as e:
            logger.error(f"Error during cleanup of collection {collection_name}: {str(e)}")

    def test_connection(self, config: Dict) -> bool:
        """Test connection to Qdrant with provided configuration"""
        try:
            test_client = QdrantClient(**config)
            # Try to get collection info to verify access
            collection_info = test_client.get_collection(collection_name=config["collection_name"])
            return True
        except Exception as e:
            logger.error(f"Qdrant connection test failed: {str(e)}")
            return False
