import weaviate
from typing import Dict, Optional
import secrets
from weaviate.classes.config import Configure
from weaviate.classes.tenants import Tenant, TenantActivityStatus
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout, Auth
from weaviate.classes.rbac import Permissions

from app.models.mongodb.client import Client
from app.models.mongodb.client_data_store import ClientDataStore, DatabaseType
from app.models.mongodb.client_data_store_tenant import ClientDataStoreTenant
from app.models.schemas.database_config import WeaviateConfig
from app.models.mongodb.utils import CredentialManager
from app.utils.logger import get_logger
from .base import BaseDataStoreService

logger = get_logger(__name__)


class WeaviateService(BaseDataStoreService):
    """Service for managing Weaviate vector databases with multi-tenant support"""

    def __init__(self, admin_connection: WeaviateConfig, credential_manager: "CredentialManager"):
        super().__init__(admin_connection, credential_manager)
        self.client = weaviate.WeaviateClient(
            connection_params=ConnectionParams.from_url(
                admin_connection.url,
            ),
            auth_client_secret=Auth.api_key(admin_connection.api_key),
            additional_config=AdditionalConfig(timeout=Timeout(**admin_connection.timeout_config)),
            skip_init_checks=False,
        )

    def create_database(self, client: Client) -> ClientDataStore:
        """Create a new Weaviate collection for a client"""
        try:
            self._check_data_store_limit(client)

            # Generate unique class name for the client
            class_name = f"Client{client.client_id.replace('-', '')}"

            # Create collection with multi-tenancy enabled
            self.client.collections.create(
                name=class_name,
                description=f"Vector store for client {client.name}",
                multi_tenancy_config=Configure.multi_tenancy(enabled=True, auto_tenant_creation=False),
            )

            # Create client-specific config
            config = WeaviateConfig(
                url=self.admin_connection.url,
                api_key=self.get_readonly_collection_api_key(class_name=class_name),
                class_name=class_name,
                additional_headers=self.admin_connection.additional_headers,
                timeout_config=self.admin_connection.timeout_config,
            )

            # Create data store record
            data_store = ClientDataStore(
                client=client,
                database_type=DatabaseType.WEAVIATE,
                config=self.credential_manager.encrypt_config(config.model_dump()),
                is_active=True,
            )
            data_store.save()

            logger.info(f"Created Weaviate collection for client: {client.client_id}")
            return data_store

        except Exception as e:
            logger.error(f"Error creating Weaviate collection for client {client.client_id}", exc_info=True)
            self._cleanup_failed_creation(class_name)
            raise ValueError(f"Failed to create Weaviate collection: {str(e)}")

    def create_tenant(
        self, data_store: ClientDataStore, tenant_id: str, name: str, metadata: Optional[Dict] = None
    ) -> ClientDataStoreTenant:
        """Create a new tenant under an existing data store"""
        try:
            config = WeaviateConfig(**self.credential_manager.decrypt_config(data_store.config))
            collection = self.client.collections.get(config.class_name)

            collection.tenants.create([Tenant(name=tenant_id, activity_status=TenantActivityStatus.ACTIVE)])

            tenant = ClientDataStoreTenant(
                client_data_store=data_store, tenant_id=tenant_id, name=name, metadata=metadata or {}, is_active=True
            )
            tenant.save()

            logger.info(f"Created tenant {tenant_id} for data store {data_store.id}")
            return tenant

        except Exception as e:
            logger.error(f"Error creating tenant for data store {data_store.id}", exc_info=True)
            raise ValueError(f"Failed to create tenant: {str(e)}")

    def deactivate_tenant(self, data_store: ClientDataStore, tenant_id: str) -> None:
        """Deactivate a tenant (sets to INACTIVE state)"""
        try:
            config = WeaviateConfig(**self.credential_manager.decrypt_config(data_store.config))
            collection = self.client.collections.get(config.class_name)

            # Update tenant status in Weaviate
            collection.tenants.update([Tenant(name=tenant_id, activity_status=TenantActivityStatus.INACTIVE)])

            # Update tenant record
            tenant = ClientDataStoreTenant.objects.get(client_data_store=data_store, tenant_id=tenant_id)
            tenant.is_active = False
            tenant.save()

            logger.info(f"Deactivated tenant {tenant_id} in data store {data_store.id}")

        except Exception as e:
            logger.error(f"Error deactivating tenant {tenant_id}", exc_info=True)
            raise ValueError(f"Failed to deactivate tenant: {str(e)}")

    def delete_tenant(self, data_store: ClientDataStore, tenant_id: str) -> None:
        """Permanently delete a tenant and its data"""
        try:
            config = WeaviateConfig(**self.credential_manager.decrypt_config(data_store.config))
            collection = self.client.collections.get(config.class_name)

            # Delete tenant from Weaviate
            collection.tenants.remove([tenant_id])

            # Delete tenant record
            tenant = ClientDataStoreTenant.objects.get(client_data_store=data_store, tenant_id=tenant_id)
            tenant.delete()

            logger.info(f"Deleted tenant {tenant_id} from data store {data_store.id}")

        except Exception as e:
            logger.error(f"Error deleting tenant {tenant_id}", exc_info=True)
            raise ValueError(f"Failed to delete tenant: {str(e)}")

    def get_readonly_collection_api_key(self, class_name: str) -> str:
        """Create read-only config for a data store"""
        try:

            # Generate read-only API key
            readonly_api_key = f"wv_ro_{secrets.token_urlsafe(32)}"

            # Setup read-only permissions
            readonly_permissions = [
                Permissions.collections(
                    collection=class_name,
                    read_config=True,
                ),
                Permissions.data(collection=class_name, read=True),
            ]

            # Create read-only role
            role_name = f"{class_name}_readonly"
            self.client.roles.create(
                role_name=role_name,
                permissions=readonly_permissions,
                description=f"Read-only role for {class_name}",
            )

            # Assign role to readonly API key
            self.client.roles.assign_to_user(role_names=[role_name], user=readonly_api_key)

            return readonly_api_key

        except Exception as e:
            logger.error(f"Error creating read-only config for class_name {class_name}", exc_info=True)
            raise ValueError(f"Failed to create read-only config: {str(e)}")

    def _cleanup_failed_creation(self, class_name: str) -> None:
        """Cleanup if class creation fails"""
        try:
            collection = self.client.collections.get(class_name)
            if collection:
                collection.delete()
        except Exception as e:
            logger.error(f"Error during cleanup of class {class_name}: {str(e)}")

    def test_connection(self, config: Dict) -> bool:
        """Test connection to Weaviate with provided configuration"""
        try:
            test_client = weaviate.Client(
                url=config["url"], auth_client_secret=weaviate.AuthApiKey(api_key=config["api_key"])
            )
            if config.get("class_name"):
                test_client.collections.get(config["class_name"])
            return True
        except Exception as e:
            logger.error(f"Weaviate connection test failed: {str(e)}")
            return False
