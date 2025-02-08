from abc import ABC, abstractmethod
import secrets
import string
from typing import Tuple, Dict, List, Any
from app.models.mongodb.client import Client
from app.models.mongodb.client_data_store import ClientDataStore
from app.models.mongodb.utils import CredentialManager
from app.models.mongodb.enums import EngineType


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

    def _check_data_store_limit(self, client: Client, engine_type: EngineType) -> None:
        """Check if client has reached their data store limit for given engine type"""
        current_stores = ClientDataStore.objects(client=client, engine_type=engine_type.value, is_active=True).count()

        if engine_type == EngineType.STRUCTURED:
            max_stores = client.max_structured_data_stores if hasattr(client, "max_structured_stores") else 1
        else:
            max_stores = client.max_unstructured_data_stores if hasattr(client, "max_unstructured_stores") else 1

        if current_stores >= max_stores:
            raise ValueError(f"Client has reached maximum number of {engine_type.value} data stores ({max_stores})")

    @abstractmethod
    def create_database(self, client: Client) -> "ClientDataStore":
        """Create a new database for a client"""
        pass

    @abstractmethod
    def raw_execute(self, config: Dict[str, Any], query: str, params: Dict = None) -> List[tuple]:
        """Execute raw query and return results"""
        pass


    @abstractmethod
    def test_connection(self, config: dict) -> bool:
        """Test database connection"""
        pass
