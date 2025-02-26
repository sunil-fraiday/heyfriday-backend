from typing import Dict, Any, Optional
import requests
import json
import pika
from pika.exceptions import AMQPError

from app.models.mongodb.events.event_processor_config import EventProcessorConfig, ProcessorType
from app.services.events.event_delivery_tracking import EventDeliveryTrackingService
from app.models.mongodb.events.event_delivery_attempt import AttemptStatus
from app.models.schemas.processor_config import HttpWebhookConfig, AmqpConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProcessorDispatchService:
    """
    Service for dispatching events to configured processors.
    """

    @staticmethod
    def dispatch_to_processor(
        processor: EventProcessorConfig, event_data: Dict[str, Any], delivery_id: Optional[str] = None
    ) -> bool:
        """
        Dispatch an event to a specific processor based on its type.
        Returns success status (true/false).

        Args:
            processor: The processor configuration
            event_data: The event data to send
            delivery_id: Optional ID of a delivery record to update
        """
        try:
            processor_type = processor.processor_type

            # Validate config before dispatching
            processor.validate_config()

            success = False
            response_status = None
            response_body = None
            error_message = None

            if processor_type == ProcessorType.HTTP_WEBHOOK:
                config = HttpWebhookConfig(**processor.config)
                success, response_status, response_body, error_message = (
                    ProcessorDispatchService._dispatch_http_webhook(config, event_data)
                )

            elif processor_type == ProcessorType.AMQP:
                config = AmqpConfig(**processor.config)
                success, error_message = ProcessorDispatchService._dispatch_amqp(config, event_data)

            else:
                logger.error(f"Unsupported processor type: {processor_type}")
                error_message = f"Unsupported processor type: {processor_type}"
                success = False

            # Update delivery record if provided
            if delivery_id:
                EventDeliveryTrackingService.record_attempt(
                    delivery_id=delivery_id,
                    status=AttemptStatus.SUCCESS if success else AttemptStatus.FAILURE,
                    response_status=response_status,
                    response_body=response_body,
                    error_message=error_message,
                )

            return success

        except Exception as e:
            logger.error(f"Error dispatching to processor {processor.name}", exc_info=True)

            # Update delivery record if provided
            if delivery_id:
                EventDeliveryTrackingService.record_attempt(
                    delivery_id=delivery_id, status=AttemptStatus.FAILURE, error_message=str(e)
                )

            return False

    @staticmethod
    def _dispatch_http_webhook(config: HttpWebhookConfig, event_data: Dict[str, Any]) -> bool:
        """
        Dispatch event to HTTP webhook.
        """
        try:
            webhook_url = str(config.webhook_url)

            response = requests.post(webhook_url, json=event_data, headers=config.headers, timeout=config.timeout)

            try:
                response_body = response.json()
            except:
                response_body = {"text": response.text}

            # Check for success
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Successfully dispatched to webhook {webhook_url}")
                return True, response.status_code, response_body, None
            else:
                error_msg = f"Failed webhook dispatch: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, response.status_code, response_body, error_msg

        except requests.RequestException as e:
            logger.error(f"HTTP error dispatching to webhook", exc_info=True)
            return False, None, None, str(e)

    @staticmethod
    def _dispatch_amqp(config: AmqpConfig, event_data: Dict[str, Any]) -> bool:
        """
        Dispatch event to AMQP broker (e.g., RabbitMQ).
        """
        try:
            credentials = None
            if config.username and config.password:
                credentials = pika.PlainCredentials(config.username, config.password)

            connection_params = pika.ConnectionParameters(
                host=config.host, port=config.port, virtual_host=config.vhost, credentials=credentials
            )

            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()

            properties = pika.BasicProperties(delivery_mode=2, content_type="application/json")

            channel.basic_publish(
                exchange=config.exchange,
                routing_key=config.routing_key,
                body=json.dumps(event_data),
                properties=properties,
            )

            connection.close()

            logger.info(f"Successfully published to AMQP exchange={config.exchange}, routing_key={config.routing_key}")
            return True, None

        except AMQPError as e:
            logger.error(f"AMQP error dispatching event", exc_info=True)
            return False, str(e)
        except Exception as e:
            logger.error(f"Error dispatching to AMQP", exc_info=True)
            return False, str(e)
