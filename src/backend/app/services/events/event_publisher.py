from typing import Dict, Optional, Any

from app.models.mongodb.events.event_types import EventType, EntityType
from app.services.events.event import EventService
from app.utils.logger import get_logger
from app.tasks.events import process_event

logger = get_logger(__name__)


class EventPublisher:
    """
    Publishes events to the system and initiates async processing.
    """
    
    @staticmethod
    def publish(
        event_type: EventType,
        entity_type: EntityType,
        entity_id: str,
        parent_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Publish an event to the system.
        
        1. Creates and saves the event to the database
        2. Triggers async processing of the event
        3. Returns the event ID
        """
        try:
            # Create and save the event
            event = EventService.create_event(
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                parent_id=parent_id,
                data=data or {}
            )
            
            # Trigger async processing
            process_event.delay(
                event_id=str(event.id),
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                parent_id=parent_id,
                data=data or {}
            )
            
            logger.info(f"Published event {event_type} for {entity_type}:{entity_id}")
            return str(event.id)
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type} for {entity_type}:{entity_id}", exc_info=True)
            # In fire-and-forget, we still want to know if publishing failed
            # but we don't want to break the caller's flow
            # Re-raise the exception so caller can decide how to handle it
            raise