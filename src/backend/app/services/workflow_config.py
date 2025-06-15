"""
Service for managing workflow configurations.
"""
from typing import List, Optional, Dict, Any

from app.models.mongodb.workflow_config import WorkflowConfig
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowConfigService:
    """
    Service for managing workflow configurations.
    """

    @staticmethod
    def get_workflow_id(client_id: str, client_channel_id: Optional[str]) -> str:
        """
        Get workflow ID based on client and channel with fallback mechanism:
        1. Try client-channel specific config if client_channel_id is provided
        2. Fall back to client-level config
        3. Fall back to default from environment

        Args:
            client_id: The client ID
            client_channel_id: Optional client channel ID

        Returns:
            The workflow ID to use
        """
        # Use default workflow if feature flag is disabled
        if not settings.ENABLE_CONFIGURABLE_WORKFLOWS:
            return settings.SLACK_AI_SERVICE_WORKFLOW_ID

        # Try to find channel-specific config if client_channel_id is provided
        if client_channel_id:
            config = WorkflowConfig.objects(
                client=client_id,
                client_channel=client_channel_id,
                is_active=True
            ).first()

            if config:
                logger.info(
                    f"Using channel-specific workflow ID {config.workflow_id} for client {client_id}, "
                    f"channel {client_channel_id}"
                )
                return config.workflow_id

        # Fall back to client-level config
        config = WorkflowConfig.objects(
            client=client_id,
            client_channel=None,
            is_active=True
        ).first()

        if config:
            logger.info(
                f"Using client-level workflow ID {config.workflow_id} for client {client_id}"
            )
            return config.workflow_id

        # Fall back to default if no config exists
        logger.info(
            f"No workflow config found for client {client_id}. "
            f"Using default workflow ID from environment."
        )
        return settings.SLACK_AI_SERVICE_WORKFLOW_ID

    @staticmethod
    def create_workflow_config(config_data: Dict[str, Any]) -> WorkflowConfig:
        """
        Create a new workflow configuration.

        Args:
            config_data: The configuration data

        Returns:
            The created workflow configuration
        """
        workflow_config = WorkflowConfig(**config_data)
        workflow_config.save()
        logger.info(f"Created workflow config {workflow_config.id} for client {workflow_config.client.id}")
        return workflow_config

    @staticmethod
    def update_workflow_config(config_id: str, config_data: Dict[str, Any]) -> WorkflowConfig:
        """
        Update an existing workflow configuration.

        Args:
            config_id: The ID of the configuration to update
            config_data: The updated configuration data

        Returns:
            The updated workflow configuration
        """
        workflow_config = WorkflowConfig.objects.get(id=config_id)
        
        for key, value in config_data.items():
            setattr(workflow_config, key, value)
        
        workflow_config.save()
        logger.info(f"Updated workflow config {workflow_config.id}")
        return workflow_config

    @staticmethod
    def get_workflow_config(config_id: str) -> WorkflowConfig:
        """
        Get a workflow configuration by ID.

        Args:
            config_id: The ID of the configuration to get

        Returns:
            The workflow configuration
        """
        return WorkflowConfig.objects.get(id=config_id)

    @staticmethod
    def delete_workflow_config(config_id: str) -> bool:
        """
        Delete a workflow configuration.

        Args:
            config_id: The ID of the configuration to delete

        Returns:
            True if the configuration was deleted, False otherwise
        """
        workflow_config = WorkflowConfig.objects.get(id=config_id)
        workflow_config.delete()
        logger.info(f"Deleted workflow config {config_id}")
        return True

    @staticmethod
    def list_workflow_configs(
        client_id: Optional[str] = None,
        client_channel_id: Optional[str] = None
    ) -> List[WorkflowConfig]:
        """
        List workflow configurations with optional filtering.

        Args:
            client_id: Optional client ID to filter by
            client_channel_id: Optional client channel ID to filter by

        Returns:
            List of workflow configurations matching the filters
        """
        query = {}
        
        if client_id:
            query["client"] = client_id
        
        if client_channel_id:
            query["client_channel"] = client_channel_id
        

        
        return WorkflowConfig.objects(**query)
