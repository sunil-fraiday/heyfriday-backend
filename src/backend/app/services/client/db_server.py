from typing import Optional

from app.utils.logger import get_logger
from app.models.mongodb.client import Client
from app.models.mongodb.client_db_server import ClientDBServer
from app.models.mongodb.enums import DatabaseType
from app.models.mongodb.utils import CredentialManager
from app.models.schemas.database_config import DatabaseConfig

logger = get_logger(__name__)


class DBServerService:
    def __init__(self, credential_manager: "CredentialManager"):
        self.credential_manager = credential_manager

    def get_client_db_server(self, client_id: str, database_type: DatabaseType) -> dict:
        """
        Get database server configuration:
        1. If client has their own server(s), use the active one
        2. Otherwise, use the global default server
        """
        try:
            client = Client.objects.get(client_id=client_id)

            # First check if client has any active servers
            client_servers = ClientDBServer.objects(client=client, server_type=database_type, is_active=True)

            if client_servers.count() > 0:
                # Client has their own server(s), use the first active one
                server = client_servers.first()
                logger.info(f"Using client-specific {database_type} server for {client_id}")
                return server.get_config(self.credential_manager).model_dump()

            # No client-specific server, look for global default
            default_server = ClientDBServer.objects(
                client=None, server_type=database_type, is_default=True, is_active=True
            ).first()

            if not default_server:
                raise ValueError(
                    f"No available {database_type} server found. Neither client-specific "
                    f"nor global default server exists."
                )

            logger.info(f"Using global default {database_type} server for {client_id}")
            return default_server.get_config(self.credential_manager).model_dump()

        except Client.DoesNotExist:
            raise ValueError(f"Client not found: {client_id}")
        except Exception as e:
            logger.error(f"Error getting DB server for client {client_id}", exc_info=True)
            raise

    def create_server(
        self,
        database_type: DatabaseType,
        config: DatabaseConfig,
        client_id: Optional[str] = None,
        is_default: bool = False,
    ) -> ClientDBServer:
        """Create a new database server configuration"""
        try:
            if client_id:
                client = Client.objects.get(client_id=client_id)
                if is_default:
                    raise ValueError(
                        "Client-specific servers cannot be marked as default. "
                        "The is_default flag is reserved for global servers."
                    )
            else:
                client = None

            # Encrypt sensitive configuration
            encrypted_config = self.credential_manager.encrypt_config(config.model_dump())

            server = ClientDBServer(
                server_type=database_type,
                config=encrypted_config,
                client=client,
                is_default=is_default and client is None,
                is_active=True,
            )
            server.save()

            logger.info(
                f"Created new {database_type} server "
                f"{'for client ' + client_id if client_id else 'as global default'}"
            )
            return server

        except Client.DoesNotExist:
            raise ValueError(f"Client not found: {client_id}")
        except Exception as e:
            logger.error(
                f"Error creating DB server" f"{' for client ' + client_id if client_id else ''}", exc_info=True
            )
            raise
