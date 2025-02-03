from typing import Optional
from app.models.mongodb.client import Client
from app.models.mongodb.semantic_layer.client_semantic_server import ClientSemanticServer
from app.models.mongodb.semantic_layer.config_models import SemanticLayerConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ClientSemanticServerService:
    """Service for managing semantic layer server configurations"""

    def get_client_semantic_server(self, client_id: str) -> ClientSemanticServer:
        """
        Get semantic server configuration:
        1. If client has their own server(s), use the active one
        2. Otherwise, use the global default server
        """
        try:
            client = Client.objects.get(client_id=client_id)

            # First check if client has any active servers
            client_servers = ClientSemanticServer.objects(client=client, is_active=True)

            if client_servers.count() > 0:
                server = client_servers.first()
                logger.info(f"Using client-specific semantic server for {client_id}")
                return server

            # No client-specific server, look for global default
            default_server = ClientSemanticServer.objects(client=None, is_default=True, is_active=True).first()

            if not default_server:
                raise ValueError(
                    "No available semantic server found. Neither client-specific nor global default server exists."
                )

            logger.info(f"Using global default semantic server for {client_id}")
            return default_server

        except Client.DoesNotExist:
            raise ValueError(f"Client not found: {client_id}")
        except Exception as e:
            logger.error(f"Error getting semantic server for client {client_id}", exc_info=True)
            raise

    def create_semantic_server(
        self,
        server_name: str,
        server_url: str,
        semantic_config: SemanticLayerConfig,
        client_id: Optional[str] = None,
        is_default: bool = False,
    ) -> ClientSemanticServer:
        """Create a new semantic server configuration"""
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

            server = ClientSemanticServer(
                server_name=server_name,
                server_url=server_url,
                semantic_config=semantic_config,
                client=client,
                is_default=is_default and client is None,
                is_active=True,
            )
            server.save()

            logger.info(
                f"Created new semantic server '{server_name}' "
                f"{'for client ' + client_id if client_id else 'as global default'}"
            )
            return server

        except Client.DoesNotExist:
            raise ValueError(f"Client not found: {client_id}")
        except Exception as e:
            logger.error(f"Error creating semantic server", exc_info=True)
            raise ValueError(f"Failed to create semantic server: {str(e)}")
