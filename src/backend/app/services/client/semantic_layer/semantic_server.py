from typing import Optional, List
from fastapi import status
from fastapi.exceptions import HTTPException

from app.models.mongodb.client import Client
from app.schemas.client.semantic_layer.semantic_server import SemanticConfigCreate
from app.models.mongodb.semantic_layer.client_semantic_server import ClientSemanticServer
from app.models.mongodb.semantic_layer.config_models import SemanticEngineType
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
            raise HTTPException(status=status.HTTP_404_NOT_FOUND, detail=f"Client not found: {client_id}")
        except Exception as e:
            logger.error(f"Error getting semantic server for client {client_id}", exc_info=True)
            raise

    def create_semantic_server(
        self,
        server_name: str,
        engine_type: SemanticEngineType,
        semantic_config: SemanticConfigCreate,
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
                engine_type=engine_type,
                semantic_config=semantic_config.model_dump(),
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

    def list_semantic_servers(
        self, client_id: Optional[str] = None, skip: int = 0, limit: int = 50, include_inactive: bool = False
    ) -> List[ClientSemanticServer]:
        """List semantic servers with optional filtering"""
        try:
            query = {}
            if client_id:
                query["client"] = client_id
            if not include_inactive:
                query["is_active"] = True

            servers = ClientSemanticServer.objects(**query).order_by("-created_at").skip(skip).limit(limit)

            return list(servers)
        except Exception as e:
            logger.error("Error listing semantic servers", exc_info=True)
            raise ValueError(str(e))

    def count_semantic_servers(self, client_id: Optional[str] = None, include_inactive: bool = False) -> int:
        """Count total semantic servers matching filter"""
        try:
            query = {}
            if client_id:
                query["client"] = client_id
            if not include_inactive:
                query["is_active"] = True

            return ClientSemanticServer.objects(**query).count()
        except Exception as e:
            logger.error("Error counting semantic servers", exc_info=True)
            raise ValueError(str(e))

    def get_semantic_server(self, server_id: str) -> ClientSemanticServer:
        """Get a specific semantic server configuration"""
        try:
            server = ClientSemanticServer.objects.get(id=server_id)
            return server
        except ClientSemanticServer.DoesNotExist:
            raise HTTPException(status=status.HTTP_404_NOT_FOUND, detail=f"Semantic server not found: {server_id}")
        except Exception as e:
            logger.error(f"Error getting semantic server {server_id}", exc_info=True)
            raise
