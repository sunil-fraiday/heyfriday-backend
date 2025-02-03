from typing import Optional
from fastapi.exceptions import HTTPException
from fastapi import status

from app.utils.logger import get_logger
from app.models.mongodb.client import Client
from app.models.mongodb.client_data_store import ClientDataStore
from app.models.mongodb.semantic_layer.client_semantic_layer import ClientSemanticLayer
from app.services.client.semantic_layer.repository import ClientRepositoryService
from app.services.client.semantic_layer.semantic_server import ClientSemanticServerService
from app.services.client.semantic_layer.github import GitHubService


logger = get_logger(__name__)


class ClientSemanticLayerService:
    """Service for managing semantic layers"""

    def create_semantic_layer(
        self,
        client_id: str,
    ) -> ClientSemanticLayer:
        """Create a new semantic layer for a client"""
        try:
            client: Client = Client.objects.get(client_id=client_id)

            semantic_server_service = ClientSemanticServerService()
            repository_service = ClientRepositoryService()
            github_service = GitHubService()

            semantic_server = semantic_server_service.get_client_semantic_server(client_id=client.client_id)
            repository = repository_service.get_client_repository(client_id=client.client_id)

            # Validate repository access
            if not github_service.validate_repository_access(repository):
                raise ValueError("Invalid repository access. Please check credentials and permissions.")

            # Create client folder in repository
            folder_name = str(client.client_id)  # Use client ID as folder name
            github_service.create_folder(repository, folder_name)

            # Create semantic layer
            semantic_layer = ClientSemanticLayer(
                client=client,
                repository=repository,
                semantic_server=semantic_server,
                repository_folder=folder_name,
                is_active=True,
            )
            semantic_layer.save()

            logger.info(f"Created semantic layer for client {client_id}")
            return semantic_layer

        except Exception as e:
            logger.error(f"Error creating semantic layer for client {client_id}", exc_info=True)
            raise ValueError(f"Failed to create semantic layer: {str(e)}")

    def add_data_store(self, semantic_layer_id: str, data_store_id: str) -> ClientSemanticLayer:
        """Add a data store to semantic layer"""
        try:
            semantic_layer = ClientSemanticLayer.objects.get(id=semantic_layer_id)
            data_store = ClientDataStore.objects.get(id=data_store_id)

            # Validate data store belongs to same client
            if data_store.client.id != semantic_layer.client.id:
                raise ValueError("Data store does not belong to the semantic layer's client")

            # Add to data stores if not already present
            if data_store not in semantic_layer.data_stores:
                semantic_layer.data_stores.append(data_store)
                semantic_layer.save()

                logger.info(f"Added data store {data_store_id} to semantic layer {semantic_layer_id}")

            return semantic_layer

        except ClientSemanticLayer.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Semantic layer not found: {semantic_layer_id}"
            )
        except ClientDataStore.DoesNotExist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Data store not found: {data_store_id}")
        except Exception as e:
            logger.error(f"Error adding data store to semantic layer", exc_info=True)
            raise RuntimeError(str(e))

    def remove_data_store(self, semantic_layer_id: str, data_store_id: str) -> ClientSemanticLayer:
        """Remove a data store from semantic layer"""
        try:
            semantic_layer = ClientSemanticLayer.objects.get(id=semantic_layer_id)
            data_store = ClientDataStore.objects.get(id=data_store_id)

            if data_store in semantic_layer.data_stores:
                semantic_layer.data_stores.remove(data_store)
                semantic_layer.save()

                logger.info(f"Removed data store {data_store_id} from semantic layer {semantic_layer_id}")

            return semantic_layer

        except (ClientSemanticLayer.DoesNotExist, ClientDataStore.DoesNotExist) as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Error removing data store from semantic layer", exc_info=True)
            raise RuntimeError(str(e))

    def deactivate_semantic_layer(self, semantic_layer_id: str) -> None:
        """Deactivate a semantic layer"""
        try:
            semantic_layer = ClientSemanticLayer.objects.get(id=semantic_layer_id)
            semantic_layer.is_active = False
            semantic_layer.save()

            logger.info(f"Deactivated semantic layer {semantic_layer_id}")

        except ClientSemanticLayer.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Semantic layer not found: {semantic_layer_id}"
            )
        except Exception as e:
            logger.error(f"Error deactivating semantic layer", exc_info=True)
            raise RuntimeError(str(e))
