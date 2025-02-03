from typing import Optional, List
from github import Github, GithubException
from pathlib import Path

from app.models.mongodb.semantic_layer.client_repository import ClientRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GitHubService:
    """Service for handling GitHub operations"""

    def validate_repository_access(self, repository: ClientRepository) -> bool:
        """
        Validate repository access and permissions
        Returns True if repository is accessible and has correct permissions
        """
        try:
            client = Github(repository.repository_config.api_key)
            repo = client.get_repo(self._get_repo_name(repository.repository_config.repo_url))

            # Check branch exists
            branch = repo.get_branch(repository.repository_config.branch)

            # Test file operations
            test_path = f"{repository.repository_config.base_path}/.test"
            test_content = "test"

            # Try to create a test file
            repo.create_file(
                test_path, "Test repository access", test_content, branch=repository.repository_config.branch
            )

            # Clean up test file
            file_content = repo.get_contents(test_path, ref=repository.repository_config.branch)
            repo.delete_file(
                test_path, "Clean up test file", file_content.sha, branch=repository.repository_config.branch
            )

            return True

        except GithubException as e:
            logger.error(f"GitHub validation failed: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error during validation: {str(e)}", exc_info=True)
            return False

    def create_folder(self, repository: ClientRepository, folder_path: str) -> bool:
        """
        Create a folder in the repository by creating a .gitkeep file
        Returns True if successful
        """
        try:
            client = Github(repository.repository_config.api_key)
            repo = client.get_repo(self._get_repo_name(repository.repository_config.repo_url))

            full_path = self._join_paths(repository.repository_config.base_path, folder_path, ".gitkeep")

            repo.create_file(
                full_path, f"Initialize {folder_path} folder", "", branch=repository.repository_config.branch
            )

            return True

        except GithubException as e:
            logger.error(f"Failed to create folder {folder_path}: {str(e)}", exc_info = True)
            raise RuntimeError(f"Failed to create folder: {str(e)}")

    def write_file(self, repository: ClientRepository, file_path: str, content: str, commit_message: str) -> bool:
        """Write or update a file in the repository"""
        try:
            client = Github(repository.repository_config.api_key)
            repo = client.get_repo(self._get_repo_name(repository.repository_config.repo_url))

            full_path = self._join_paths(repository.repository_config.base_path, file_path)

            try:
                # Try to get existing file
                file_content = repo.get_contents(full_path, ref=repository.repository_config.branch)
                # Update file if it exists
                repo.update_file(
                    full_path, commit_message, content, file_content.sha, branch=repository.repository_config.branch
                )
            except GithubException:
                # Create new file if it doesn't exist
                repo.create_file(full_path, commit_message, content, branch=repository.repository_config.branch)

            return True

        except GithubException as e:
            logger.error(f"Failed to write file {file_path}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to write file: {str(e)}")

    def read_file(self, repository: ClientRepository, file_path: str) -> Optional[str]:
        """Read file content from repository"""
        try:
            client = Github(repository.repository_config.api_key)
            repo = client.get_repo(self._get_repo_name(repository.repository_config.repo_url))

            full_path = self._join_paths(repository.repository_config.base_path, file_path)

            file_content = repo.get_contents(full_path, ref=repository.repository_config.branch)
            return file_content.decoded_content.decode("utf-8")

        except GithubException as e:
            logger.error(f"Failed to read file {file_path}: {str(e)}", exc_info = True)
            return None

    def list_files(self, repository: ClientRepository, folder_path: str) -> List[str]:
        """List all files in a folder"""
        try:
            client = Github(repository.repository_config.api_key)
            repo = client.get_repo(self._get_repo_name(repository.repository_config.repo_url))

            full_path = self._join_paths(repository.repository_config.base_path, folder_path)

            contents = repo.get_contents(full_path, ref=repository.repository_config.branch)
            return [content.path for content in contents if content.type == "file"]

        except GithubException as e:
            logger.error(f"Failed to list files in {folder_path}: {str(e)}", exc_info = True)
            return []

    @staticmethod
    def _get_repo_name(repo_url: str) -> str:
        """Extract repository name from URL"""
        # Handle both HTTPS and SSH URLs
        if repo_url.startswith("https://"):
            return repo_url.replace("https://github.com/", "").rstrip(".git")
        else:
            return repo_url.split(":")[-1].rstrip(".git")

    @staticmethod
    def _join_paths(*paths: str) -> str:
        """Join paths ensuring correct forward slashes"""
        return str(Path(*paths)).replace("\\", "/")
