from abc import ABC, abstractmethod
import secrets
import string
from typing import Tuple
from app.models.mongodb.client import Client
from app.models.mongodb.client_structured_data_store import ClientStructuredDataStore, CredentialManager


class BaseDataStoreService(ABC):
    """Base class for database-specific services"""

    def __init__(self, admin_connection: dict, credential_manager: "CredentialManager"):
        self.admin_connection = admin_connection
        self.credential_manager = credential_manager

    def _generate_secure_credentials(self, prefix: str) -> Tuple[str, str]:
        """Generate secure username and password"""
        username = f"{prefix}_{secrets.token_hex(6)}"
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = "".join(secrets.choice(alphabet) for _ in range(32))
        return username, password

    def _check_data_store_limit(self, client: Client) -> None:
        """Check if client has reached their data store limit"""
        current_stores = ClientStructuredDataStore.objects(client=client, is_active=True).count()

        max_stores = client.max_structured_data_stores if hasattr(client, "max_structured_data_stores") else 1

        if current_stores >= max_stores:
            raise Exception(f"Client has reached maximum number of data stores ({max_stores})")

    @abstractmethod
    def create_database(self, client: Client) -> "ClientStructuredDataStore":
        """Create a new database for a client"""
        pass

    @abstractmethod
    def test_connection(self, config: dict) -> bool:
        """Test database connection"""
        pass
