from typing import Optional, List, Dict, Any
from fastapi.exceptions import HTTPException
from fastapi import status
from slugify import slugify

from app.utils.logger import get_logger
from app.models.mongodb.client import Client
from app.models.mongodb.client_data_store import ClientDataStore
from app.models.mongodb.semantic_layer.client_semantic_layer_data_store import ClientSemanticLayerDataStore
from app.models.mongodb.semantic_layer.client_semantic_layer_data_store import (
    ClientSemanticLayerDataStore,
    RelationshipStatus,
)
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
            folder_name = slugify(f"{str(client.name)}")  # Use client ID as folder name
            github_service.create_folder(repository, folder_name)

            # Create semantic layer
            semantic_layer = ClientSemanticLayer(
                client=client,
                client_repository=repository,
                client_semantic_server=semantic_server,
                repository_folder=folder_name,
                is_active=True,
            )
            semantic_layer.save()

            logger.info(f"Created semantic layer for client {client_id}")
            return semantic_layer

        except Exception as e:
            logger.error(f"Error creating semantic layer for client {client_id}", exc_info=True)
            raise ValueError(f"Failed to create semantic layer: {str(e)}")

    def list_semantic_layers(self, client_id: str, skip: int = 0, limit: int = 50):
        """List semantic layers for a client"""
        try:
            client: Client = Client.objects.get(client_id=client_id)
            semantic_layers = (
                ClientSemanticLayer.objects(client=client).order_by("-created_at").skip(skip).limit(limit)
            )
            return semantic_layers
        except Client.DoesNotExist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        except Exception as e:
            raise ValueError(f"Failed to list semantic layers: {str(e)}")

    def get_semantic_layer(self, layer_id: str) -> Optional[ClientSemanticLayer]:
        """Get a semantic layer by ID"""
        try:
            semantic_layer = ClientSemanticLayer.objects.get(id=layer_id)
            return semantic_layer
        except ClientSemanticLayer.DoesNotExist:
            return None

    def add_data_store(
        self, semantic_layer_id: str, data_store_id: str, config: Optional[Dict] = None
    ) -> ClientSemanticLayerDataStore:
        """Add a data store to semantic layer"""
        try:
            semantic_layer = ClientSemanticLayer.objects.get(id=semantic_layer_id)

            # Check if relationship already exists
            existing = ClientSemanticLayerDataStore.objects(
                client_semantic_layer=semantic_layer, client_data_store=data_store_id
            ).first()

            if existing:
                if existing.status == RelationshipStatus.INACTIVE:
                    existing.status = RelationshipStatus.ACTIVE
                    existing.save()
                    return existing
                raise ValueError("Data store already added to this semantic layer")

            relationship = ClientSemanticLayerDataStore(
                client_semantic_layer=semantic_layer,
                client_data_store=data_store_id,
                config=config or {},
                status=RelationshipStatus.PENDING,
            )
            relationship.save()

            logger.info(f"Added data store {data_store_id} to semantic layer {semantic_layer_id}")
            return relationship

        except ClientSemanticLayer.DoesNotExist:
            logger.error(f"Semantic layer not found: {semantic_layer_id}", exc_info=True)
            raise ValueError(f"Semantic layer not found: {semantic_layer_id}")
        except Exception as e:
            logger.error(f"Error adding data store to semantic layer", exc_info=True)
            raise ValueError(str(e))

    def remove_data_store(self, semantic_layer_id: str, data_store_id: str) -> None:
        """Remove a data store from semantic layer"""
        try:
            relationship = ClientSemanticLayerDataStore.objects.get(
                client_semantic_layer=semantic_layer_id,
                client_data_store=data_store_id,
                status=RelationshipStatus.ACTIVE,
            )

            relationship.status = RelationshipStatus.INACTIVE
            relationship.save()

            logger.info(f"Removed data store {data_store_id} from semantic layer {semantic_layer_id}")

        except ClientSemanticLayerDataStore.DoesNotExist:
            logger.error(
                f"Relationship not found for semantic layer {semantic_layer_id} and data store {data_store_id}",
                exc_info=True,
            )
            raise ValueError("Data store not found in this semantic layer")
        except Exception as e:
            logger.error(f"Error removing data store from semantic layer", exc_info=True)
            raise ValueError(str(e))

    def list_data_stores(self, semantic_layer_id: str, skip: int = 0, limit: int = 50) -> List[ClientDataStore]:
        """
        List data stores for a semantic layer with pagination
        Returns tuple of (data_stores, total_count)
        """
        try:
            semantic_layer = ClientSemanticLayer.objects.get(id=semantic_layer_id)

            data_stores = (
                ClientDataStore.objects(
                    id__in=[
                        rel.client_data_store.id
                        for rel in ClientSemanticLayerDataStore.objects(client_semantic_layer=semantic_layer)
                    ]
                )
                .order_by("-created_at")
                .skip(skip)
                .limit(limit)
            )

            return data_stores

        except ClientSemanticLayer.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Semantic layer not found: {semantic_layer_id}"
            )
        except Exception as e:
            logger.error("Error listing data stores", exc_info=True)
            raise ValueError(str(e))

    def get_data_store(self, semantic_layer_id: str, data_store_id: str) -> ClientDataStore:
        """Get a data store for a semantic layer"""
        try:
            semantic_layer_data_store = ClientSemanticLayerDataStore.objects.get(
                client_semantic_layer=semantic_layer_id, client_data_store=data_store_id
            )

            return semantic_layer_data_store.client_data_store
        except ClientSemanticLayerDataStore.DoesNotExist as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Semantic layer data store not found: {semantic_layer_id} {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error getting data store", exc_info=True)
            raise ValueError(str(e))

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
