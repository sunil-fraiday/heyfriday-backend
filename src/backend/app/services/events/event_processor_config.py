from typing import List, Optional, Union, Dict, Any
from pydantic import ValidationError, BaseModel

from app.models.mongodb.events.event_processor_config import EventProcessorConfig, ProcessorType
from app.models.mongodb.events.event_types import EventType, EntityType
from app.models.schemas.processor_config import HttpWebhookConfig, AmqpConfig, BaseProcessorConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProcessorConfigService:
    """
    Service for managing event processor configurations.
    """

    _config_class_map = {
        ProcessorType.HTTP_WEBHOOK: HttpWebhookConfig,
        ProcessorType.AMQP: AmqpConfig,
    }

    @staticmethod
    def create_processor_config(
        name: str,
        client_id: str,
        processor_type: ProcessorType,
        config: Union[Dict[str, Any], BaseProcessorConfig],
        event_types: List[EventType],
        entity_types: List[EntityType],
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> EventProcessorConfig:
        """
        Create a new processor configuration of any supported type.

        Args:
            name: Processor name
            client_id: Client ID
            processor_type: Type of processor (HTTP_WEBHOOK, AMQP, etc.)
            config: Configuration object or dict (will be validated based on processor_type)
            event_types: List of event types this processor handles
            entity_types: List of entity types this processor handles
            description: Optional description
            is_active: Whether the processor is active

        Returns:
            The created processor configuration

        Raises:
            ValueError: If validation fails or configuration is incorrect
        """
        try:
            config_class = ProcessorConfigService._config_class_map.get(processor_type)
            if not config_class:
                raise ValueError(f"Unsupported processor type: {processor_type}")

            if isinstance(config, dict):
                typed_config = config_class(**config)
            elif isinstance(config, config_class):
                typed_config = config
            elif isinstance(config, BaseModel):
                raise ValueError(f"Config is of type {type(config).__name__}, expected {config_class.__name__}")
            else:
                raise ValueError(f"Config must be a dict or {config_class.__name__} instance")

            processor_config = EventProcessorConfig(
                name=name,
                description=description,
                client=client_id,
                processor_type=processor_type,
                config=typed_config.model_dump(),
                event_types=[et.value for et in event_types],
                entity_types=[et.value for et in entity_types],
                is_active=is_active,
            )
            processor_config.save()

            logger.info(f"Created {processor_type} processor {name} for client {client_id}")
            return processor_config

        except ValidationError as e:
            logger.error(f"Invalid {processor_type} config: {e}", exc_info=True)
            raise ValueError(f"Invalid {processor_type} configuration: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create {processor_type} processor {name}", exc_info=True)
            raise

    @staticmethod
    def create_http_webhook_processor(
        name: str,
        client_id: str,
        config: Union[Dict[str, Any], HttpWebhookConfig],
        event_types: List[EventType],
        entity_types: List[EntityType],
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> EventProcessorConfig:
        """Convenience method to create HTTP webhook processor"""
        return ProcessorConfigService.create_processor_config(
            name=name,
            client_id=client_id,
            processor_type=ProcessorType.HTTP_WEBHOOK,
            config=config,
            event_types=event_types,
            entity_types=entity_types,
            description=description,
            is_active=is_active,
        )

    @staticmethod
    def create_amqp_processor(
        name: str,
        client_id: str,
        config: Union[Dict[str, Any], AmqpConfig],
        event_types: List[EventType],
        entity_types: List[EntityType],
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> EventProcessorConfig:
        """Convenience method to create AMQP processor"""
        return ProcessorConfigService.create_processor_config(
            name=name,
            client_id=client_id,
            processor_type=ProcessorType.AMQP,
            config=config,
            event_types=event_types,
            entity_types=entity_types,
            description=description,
            is_active=is_active,
        )

    @staticmethod
    def get_matching_processors(
        client_id: str, event_type: EventType, entity_type: EntityType
    ) -> List[EventProcessorConfig]:
        """
        Find all active processor configurations that match the given criteria.
        """
        try:
            processors = EventProcessorConfig.objects(
                client=client_id, is_active=True, event_types__in=[event_type], entity_types__in=[entity_type]
            )

            return processors

        except Exception as e:
            logger.error(f"Error finding processors for client {client_id}, event {event_type}", exc_info=True)
            return []

    @staticmethod
    def delete_processor_config(processor_id: str) -> bool:
        """
        Delete a processor configuration.
        """
        try:
            processor = EventProcessorConfig.objects.get(id=processor_id)
            processor.delete()
            logger.info(f"Deleted processor config {processor_id}")
            return True

        except EventProcessorConfig.DoesNotExist:
            logger.error(f"Processor config {processor_id} not found", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Error deleting processor config {processor_id}", exc_info=True)
            raise

    @staticmethod
    def get_processor_by_id(processor_id: str) -> Optional[EventProcessorConfig]:
        """
        Get a processor by ID.
        """
        try:
            return EventProcessorConfig.objects.get(id=processor_id)
        except EventProcessorConfig.DoesNotExist:
            logger.error(f"Processor {processor_id} not found", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error getting processor {processor_id}", exc_info=True)
            return None
