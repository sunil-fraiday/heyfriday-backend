from typing import Optional
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
        self, repository_config: RepositoryConfig, client_id: Optional[str] = None, is_default: bool = False
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
                repository_config=repository_config,
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

    def validate_repository_access(self, repository: ClientRepository) -> bool:
        """Validate repository access using credentials"""
        try:
            # TODO: Implement Git repository access validation
            # This would check if we can:
            # 1. Connect to the repository
            # 2. Have proper read/write permissions
            # 3. Access the specified branch
            return True
        except Exception as e:
            logger.error(f"Repository access validation failed", exc_info=True)
            return False
