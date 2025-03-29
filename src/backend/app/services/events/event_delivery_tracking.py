from typing import Optional, Dict, Any, List
from app.models.mongodb.events.event_delivery import EventDelivery, DeliveryStatus
from app.models.mongodb.events.event_delivery_attempt import EventDeliveryAttempt, AttemptStatus
from app.models.mongodb.events.event import Event
from app.models.mongodb.events.event_processor_config import EventProcessorConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EventDeliveryTrackingService:
    """
    Service for tracking event delivery status and attempts.
    """
    
    @staticmethod
    def create_delivery_record(
        event_id: str,
        processor_id: str,
        request_payload: Optional[Dict[str, Any]] = None,
        max_attempts: int = 3
    ) -> EventDelivery:
        """
        Create a new delivery record for an event.
        """
        try:
            delivery = EventDelivery(
                event=event_id,
                event_processor_config=processor_id,
                status=DeliveryStatus.PENDING,
                max_attempts=max_attempts,
                current_attempts=0,
                request_payload=request_payload or {}
            )
            delivery.save()
            
            logger.info(f"Created delivery record for event {event_id} to processor {processor_id}")
            return delivery
            
        except Exception as e:
            logger.error(f"Failed to create delivery record for event {event_id}", exc_info=True)
            raise
    
    @staticmethod
    def record_attempt(
        delivery_id: str,
        status: AttemptStatus,
        response_status: Optional[int] = None,
        response_body: Optional[Dict] = None,
        logs: Optional[Dict] = None
    ) -> EventDeliveryAttempt:
        """
        Record a delivery attempt.
        """
        try:
            delivery = EventDelivery.objects.get(id=delivery_id)
            
            # Increment attempt counter
            delivery.current_attempts += 1
            
            # Create attempt record
            attempt = EventDeliveryAttempt(
                event_delivery=delivery,
                attempt_number=delivery.current_attempts,
                status=status,
                response_status=response_status,
                response_body=response_body,
                logs=logs
            )
            attempt.save()
            
            # Update delivery status
            if status == AttemptStatus.SUCCESS:
                delivery.status = DeliveryStatus.COMPLETED
                
                # If successful response, try to update entity external_id
                if response_body:
                    EventDeliveryTrackingService.update_entity_external_id(
                        delivery_id=delivery_id,
                        response_body=response_body
                    )
            elif status == AttemptStatus.FAILURE and delivery.current_attempts >= delivery.max_attempts:
                delivery.status = DeliveryStatus.FAILED
            else:
                delivery.status = DeliveryStatus.IN_PROGRESS
                
            delivery.save()
            
            logger.info(f"Recorded delivery attempt {delivery.current_attempts} for {delivery_id}")
            return attempt
            
        except EventDelivery.DoesNotExist:
            logger.error(f"Delivery record {delivery_id} not found", exc_info=True)
            raise ValueError(f"Delivery record {delivery_id} not found")
        except Exception as e:
            logger.error(f"Failed to record delivery attempt for {delivery_id}", exc_info=True)
            raise
    
    @staticmethod
    def get_delivery_attempts(delivery_id: str) -> List[EventDeliveryAttempt]:
        """
        Get all attempts for a delivery.
        """
        return EventDeliveryAttempt.objects(event_delivery=delivery_id).order_by("attempt_number")
    
    @staticmethod
    def get_event_deliveries(event_id: str) -> List[EventDelivery]:
        """
        Get all deliveries for an event.
        """
        return EventDelivery.objects(event=event_id).order_by("created_at")
    
    @staticmethod
    def get_pending_deliveries(limit: int = 100) -> List[EventDelivery]:
        """
        Get pending deliveries that need processing.
        """
        return EventDelivery.objects(
            status__in=[DeliveryStatus.PENDING, DeliveryStatus.IN_PROGRESS],
            current_attempts__lt=3  # Less than max attempts
        ).order_by("created_at").limit(limit)
        
    @staticmethod
    def update_entity_external_id(
        delivery_id: str,
        response_body: Optional[Dict] = None
    ) -> bool:
        """
        Update the external_id of the entity based on the response from the webhook.
        Currently only supports CHAT_MESSAGE entities.
        
        Returns True if the entity was updated, False otherwise.
        """
        if not response_body or not isinstance(response_body, dict) or 'id' not in response_body:
            return False
            
        try:
            from app.models.mongodb.chat_message import ChatMessage
            from app.models.mongodb.events.event_types import EntityType
            
            # Get the delivery
            delivery = EventDelivery.objects.get(id=delivery_id)
            
            # Get the event
            event = delivery.event
            
            # Only process CHAT_MESSAGE entities
            if event.entity_type != EntityType.CHAT_MESSAGE:
                return False
                
            # Get the message
            message_id = event.entity_id
            message = ChatMessage.objects.get(id=message_id)
            
            # Update the external_id
            external_id = response_body.get('id')
            if external_id:
                message.external_id = str(external_id)
                message.save()
                logger.info(f"Updated external_id for message {message_id} to {external_id}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to update external_id for delivery {delivery_id}", exc_info=True)
            return False