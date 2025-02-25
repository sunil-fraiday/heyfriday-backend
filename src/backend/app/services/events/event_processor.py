from typing import Dict, Any
import requests
import json
import pika
from pika.exceptions import AMQPError

from app.models.mongodb.events.event_processor_config import EventProcessorConfig, ProcessorType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProcessorDispatchService:
    """
    Service for dispatching events to configured processors.
    Supports HTTP webhooks and AMQP (RabbitMQ).
    """
    
    @staticmethod
    def dispatch_to_processor(
        processor: EventProcessorConfig,
        event_data: Dict[str, Any]
    ) -> bool:
        """
        Dispatch an event to a specific processor based on its type.
        Returns success status (true/false).
        """
        try:
            processor_type = processor.processor_type
            
            if processor_type == ProcessorType.HTTP_WEBHOOK:
                return ProcessorDispatchService._dispatch_http_webhook(processor.config, event_data)
            
            elif processor_type == ProcessorType.AMQP:
                return ProcessorDispatchService._dispatch_amqp(processor.config, event_data)
            
            else:
                logger.error(f"Unsupported processor type: {processor_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error dispatching to processor {processor.name}", exc_info=True)
            return False
    
    @staticmethod
    def _dispatch_http_webhook(config: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Dispatch event to HTTP webhook.
        """
        try:
            webhook_url = config.get('webhook_url')
            headers = config.get('headers', {})
            timeout = config.get('timeout', 10)  # Default 10 second timeout
            
            if not webhook_url:
                logger.error("Missing webhook_url in processor config")
                return False
            
            response = requests.post(
                webhook_url,
                json=event_data,
                headers=headers,
                timeout=timeout
            )
            
            # Fire and forget, we just log the result but don't wait for success
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
    def _dispatch_amqp(config: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Dispatch event to AMQP broker (e.g., RabbitMQ).
        """
        try:
            # Extract AMQP configuration
            host = config.get('host', 'localhost')
            port = config.get('port', 5672)
            vhost = config.get('vhost', '/')
            username = config.get('username')
            password = config.get('password')
            exchange = config.get('exchange', '')
            routing_key = config.get('routing_key')
            
            if not routing_key:
                logger.error("Missing routing_key in AMQP processor config")
                return False
            
            # Set up AMQP connection
            credentials = None
            if username and password:
                credentials = pika.PlainCredentials(username, password)
            
            connection_params = pika.ConnectionParameters(
                host=host,
                port=port,
                virtual_host=vhost,
                credentials=credentials
            )
            
            # Connect and publish
            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()
            
            # Create a basic properties with delivery mode 2 (persistent)
            properties = pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
            
            # Publish the message
            channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(event_data),
                properties=properties
            )
            
            # Close the connection
            connection.close()
            
            logger.info(f"Successfully published to AMQP exchange={exchange}, routing_key={routing_key}")
            return True
            
        except AMQPError as e:
            logger.error(f"AMQP error dispatching event", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Error dispatching to AMQP", exc_info=True)
            return False