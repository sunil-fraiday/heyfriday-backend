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
                delivery=delivery,
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