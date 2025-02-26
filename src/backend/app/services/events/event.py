from typing import List, Optional, Dict
from app.models.mongodb.events.event import Event
from app.models.mongodb.events.event_types import EventType, EntityType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EventService:
    """
    Service for creating and querying events.
    """

    @staticmethod
    def create_event(
        event_type: EventType,
        entity_type: EntityType,
        entity_id: str,
        parent_id: Optional[str] = None,
        data: Optional[Dict] = None,
    ) -> Event:
        """
        Create and save a new event.
        """
        try:
            event = Event(
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                parent_id=parent_id,
                data=data or {},
            )
            event.save()
            logger.info(f"Created event: {event_type} for {entity_type}:{entity_id}")
            return event
        except Exception as e:
            logger.error(f"Error creating event {event_type} for {entity_type}:{entity_id}", exc_info=True)
            raise

    @staticmethod
    def get_entity_events(entity_type: EntityType, entity_id: str) -> List[Event]:
        """
        Get all events for a specific entity.
        """
        return Event.objects(entity_type=entity_type, entity_id=entity_id).order_by("created_at")

    @staticmethod
    def get_child_events(parent_id: str) -> List[Event]:
        """
        Get all child events for a parent entity.
        """
        return Event.objects(parent_id=parent_id).order_by("created_at")

    @staticmethod
    def get_recent_events(event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """
        Get recent events, optionally filtered by type.
        """
        query = {}
        if event_type:
            query["event_type"] = event_type

        return Event.objects(**query).order_by("-created_at").limit(limit)
    
    @staticmethod
    def get_event_by_id(event_id: str) -> Optional[Event]:
        """
        Get an event by its ID.
        """
        try:
            return Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            logger.error(f"Event {event_id} not found", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error retrieving event {event_id}", exc_info=True)
            return None

