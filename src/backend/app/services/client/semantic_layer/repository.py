from typing import Optional, List

from fastapi.exceptions import HTTPException
from app.schemas.client.semantic_layer.repository import RepositoryConfigCreate
from app.models.mongodb.client import Client
from app.models.mongodb.semantic_layer.client_repository import ClientRepository
from app.models.mongodb.semantic_layer.config_models import RepositoryConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ClientRepositoryService:
    """Service for managing semantic layer file repositories"""

    def get_client_repository(self, client_id: str) -> ClientRepository:
        """
        Get repository configuration:
        1. If client has their own repository, use the active one
        2. Otherwise, use the global default repository
        """
        try:
            client = Client.objects.get(client_id=client_id)

            # First check if client has any active repositories
            client_repos = ClientRepository.objects(client=client, is_active=True)

            if client_repos.count() > 0:
                repo = client_repos.first()
                logger.info(f"Using client-specific repository for {client_id}")
                return repo

            # No client-specific repository, look for global default
            default_repo = ClientRepository.objects(client=None, is_default=True, is_active=True).first()

            if not default_repo:
                raise ValueError(
                    "No available repository found. Neither client-specific " "nor global default repository exists."
                )

            logger.info(f"Using global default repository for {client_id}")
            return default_repo

        except Client.DoesNotExist:
            raise ValueError(f"Client not found: {client_id}")
        except Exception as e:
            logger.error(f"Error getting repository for client {client_id}", exc_info=True)
            raise

    def create_repository(
        self, repository_config: RepositoryConfigCreate, client_id: Optional[str] = None, is_default: bool = False
    ) -> ClientRepository:
        """Create a new repository configuration"""
        try:
            if client_id:
                client = Client.objects.get(client_id=client_id)
                if is_default:
                    raise ValueError(
                        "Client-specific repositories cannot be marked as default. "
                        "The is_default flag is reserved for global repositories."
                    )
            else:
                client = None

            repository = ClientRepository(
                repository_config=repository_config.model_dump(),
                client=client,
                is_default=is_default and client is None,
                is_active=True,
            )
            repository.save()

            logger.info(
                f"Created new repository {repository_config.repo_url} "
                f"{'for client ' + client_id if client_id else 'as global default'}"
            )
            return repository

        except Client.DoesNotExist:
            raise ValueError(f"Client not found: {client_id}")
        except Exception as e:
            logger.error(f"Error creating repository", exc_info=True)
            raise ValueError(f"Failed to create repository: {str(e)}")

    def list_repositories(
        self, client_id: Optional[str] = None, skip: int = 0, limit: int = 50, include_inactive: bool = False
    ) -> List[ClientRepository]:
        """List repositories with optional filtering"""
        try:
            query = {}
            if client_id:
                query["client"] = client_id
            if not include_inactive:
                query["is_active"] = True

            repositories = ClientRepository.objects(**query).order_by("-created_at").skip(skip).limit(limit)

            return repositories
        except Exception as e:
            logger.error("Error listing repositories", exc_info=True)
            raise ValueError(str(e))

    def get_repository(self, repository_id: str) -> ClientRepository:
        """ """
        try:
            repository = ClientRepository.objects.get(id=repository_id)
            return repository
        except ClientRepository.DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Repository not found: {repository_id}")

    def count_repositories(self, client_id: Optional[str] = None, include_inactive: bool = False) -> int:
        """Count total repositories matching filter"""
        try:
            query = {}
            if client_id:
                query["client"] = client_id
            if not include_inactive:
                query["is_active"] = True

            return ClientRepository.objects(**query).count()
        except Exception as e:
            logger.error("Error counting repositories", exc_info=True)
            raise ValueError(str(e))
