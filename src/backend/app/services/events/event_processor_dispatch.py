from typing import Dict, Any
import requests
import json
import pika
from pika.exceptions import AMQPError

from app.models.mongodb.events.event_processor_config import EventProcessorConfig, ProcessorType
from app.models.schemas.processor_config import HttpWebhookConfig, AmqpConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProcessorDispatchService:
    """
    Service for dispatching events to configured processors.
    """

    @staticmethod
    def dispatch_to_processor(processor: EventProcessorConfig, event_data: Dict[str, Any]) -> bool:
        """
        Dispatch an event to a specific processor based on its type.
        Returns success status (true/false).
        """
        try:
            processor_type = processor.processor_type

            # Validate config before dispatching
            processor.validate_config()

            if processor_type == ProcessorType.HTTP_WEBHOOK:
                config = HttpWebhookConfig(**processor.config)
                return ProcessorDispatchService._dispatch_http_webhook(config, event_data)

            elif processor_type == ProcessorType.AMQP:
                config = AmqpConfig(**processor.config)
                return ProcessorDispatchService._dispatch_amqp(config, event_data)

            else:
                logger.error(f"Unsupported processor type: {processor_type}")
                return False

        except Exception as e:
            logger.error(f"Error dispatching to processor {processor.name}", exc_info=True)
            return False

    @staticmethod
    def _dispatch_http_webhook(config: HttpWebhookConfig, event_data: Dict[str, Any]) -> bool:
        """
        Dispatch event to HTTP webhook.
        """
        try:
            webhook_url = str(config.webhook_url)

            response = requests.post(webhook_url, json=event_data, headers=config.headers, timeout=config.timeout)

            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Successfully dispatched to webhook {webhook_url}")
                return True
            else:
                logger.error(f"Failed webhook dispatch to {webhook_url}: {response.status_code} - {response.text}")
                return False

        except requests.RequestException as e:
            logger.error(f"HTTP error dispatching to webhook", exc_info=True)
            return False

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

            properties = pika.BasicProperties(
                delivery_mode=2, content_type="application/json"
            )

            channel.basic_publish(
                exchange=config.exchange,
                routing_key=config.routing_key,
                body=json.dumps(event_data),
                properties=properties,
            )

            connection.close()

            logger.info(f"Successfully published to AMQP exchange={config.exchange}, routing_key={config.routing_key}")
            return True

        except AMQPError as e:
            logger.error(f"AMQP error dispatching event", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Error dispatching to AMQP", exc_info=True)
            return False
