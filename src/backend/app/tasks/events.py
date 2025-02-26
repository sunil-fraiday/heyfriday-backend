from typing import Dict, Any, Optional
from celery import shared_task

from app.models.mongodb.events.event_types import EventType, EntityType
from app.services.events.event_delivery_tracking import EventDeliveryTrackingService
from app.services.events.event import EventService
from app.services.events.event_processor_dispatch import ProcessorDispatchService
from app.services.events.event_processor_config import ProcessorConfigService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _get_client_id_for_entity(entity_type: str, entity_id: str) -> Optional[str]:
    """
    Helper function to determine client_id for different entity types.
    """
    from app.models.mongodb.chat_message import ChatMessage
    from app.models.mongodb.chat_session import ChatSession

    try:
        if entity_type == EntityType.CHAT_MESSAGE:
            message = ChatMessage.objects.get(id=entity_id)
            return str(message.session.client.id)

        elif entity_type == EntityType.CHAT_SESSION:
            session = ChatSession.objects.get(id=entity_id)
            return str(session.client.id)

        elif entity_type == EntityType.AI_SERVICE:
            # For AI service events, we need to find the related chat message
            # This assumes parent_id points to a chat message
            events = EventService.get_entity_events(entity_type=EntityType.AI_SERVICE, entity_id=entity_id)
            if events and events[0].parent_id:
                return _get_client_id_for_entity(entity_type=EntityType.CHAT_MESSAGE, entity_id=events[0].parent_id)

        logger.error(f"Could not determine client_id for {entity_type}:{entity_id}")
        return None

    except Exception as e:
        logger.error(f"Error determining client_id for {entity_type}:{entity_id}", exc_info=True)
        return None


@shared_task(bind=True)
def process_event(
    self,
    event_id: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    parent_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Process an event asynchronously with delivery tracking.
    """

    try:
        # Get the original event to find the client_id
        event = EventService.get_event_by_id(event_id)
        if not event:
            logger.error(f"Event {event_id} not found")
            return {"status": "error", "message": "Event not found"}

        # Get client_id from the entity
        client_id = _get_client_id_for_entity(entity_type, entity_id)
        if not client_id:
            logger.error(f"Could not determine client_id for {entity_type}:{entity_id}")
            return {"status": "error", "message": "Client ID not found"}

        # Find matching processors for this event
        processors = ProcessorConfigService.get_matching_processors(
            client_id=client_id, event_type=event_type, entity_type=entity_type
        )

        if not processors:
            logger.info(f"No matching processors found for {event_type} event for client {client_id}")
            return {"status": "skipped", "reason": "No matching processors"}

        # Prepare event data for dispatching
        dispatch_data = {
            "event_id": event_id,
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "parent_id": parent_id,
            "data": data or {},
            "timestamp": event.created_at.isoformat(),
            "client_id": client_id,
        }

        # For each processor, create a delivery record and dispatch
        delivery_results = []
        for processor in processors:
            # Create delivery record
            delivery = EventDeliveryTrackingService.create_delivery_record(
                event_id=event_id, processor_id=str(processor.id), request_payload=dispatch_data
            )

            # Dispatch to processor with tracking
            success = ProcessorDispatchService.dispatch_to_processor(
                processor=processor, event_data=dispatch_data, delivery_id=str(delivery.id)
            )

            delivery_results.append(
                {
                    "processor_id": str(processor.id),
                    "processor_name": processor.name,
                    "delivery_id": str(delivery.id),
                    "success": success,
                }
            )

        logger.info(f"Processed event {event_id} with {len(processors)} processors")
        return {
            "status": "processed",
            "event_id": event_id,
            "client_id": client_id,
            "delivery_results": delivery_results,
        }

    except Exception as e:
        logger.error(f"Error processing event {event_id}", exc_info=True)
        # In fire-and-forget, we log the error but don't attempt to recover
        raise
