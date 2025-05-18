from typing import Tuple, Dict, Any, Optional

from app.models.mongodb.channel_request_log import EntityType
from app.services.chat.thread_manager import ThreadManager
from app.utils.logger import get_logger
from .message_payload import MessagePayloadStrategy
from .suggestion_payload import SuggestionPayloadStrategy

logger = get_logger(__name__)


class PayloadService:
    @staticmethod
    def normalize_session_id(session_id: str, client=None) -> str:
        """
        Normalize session ID for event payloads when threading is enabled.
        This ensures that external systems only see the base session ID.
        Only normalizes if threading is enabled for the client.

        Args:
            session_id: The session ID to potentially normalize
            client: The client object (optional, will be looked up if not provided)

        Returns:
            The normalized session ID if threading is enabled, otherwise original session ID
        """
        if not session_id:
            return session_id

        # Check if threading should be applied at all
        threading_enabled = False
        
        # First check by using session ID directly - this is more efficient when possible
        parent_session_id, thread_id = ThreadManager.parse_session_id(session_id)
        
        # If there's a thread component, we need to verify threading is enabled
        if thread_id:
            if client:
                # If client is provided, check its threading config
                threading_enabled, _ = ThreadManager.is_threading_enabled_for_client(client)
            else:
                # If no client, try to check threading based on session
                threading_enabled, _ = ThreadManager.is_threading_enabled_for_session(parent_session_id)
        
        if not threading_enabled:
            # Threading not enabled, return original session ID
            return session_id
            
        # Threading is enabled and session has thread component, return normalized ID
        logger.debug(f"Normalizing threaded session ID {session_id} to {parent_session_id}")
        return parent_session_id

    @staticmethod
    def _process_dict_recursively(data: Dict[str, Any], client=None) -> Dict[str, Any]:
        """
        Recursively process a dictionary to normalize any session IDs found at any level
        
        Args:
            data: Dictionary to process
            client: Optional client object for checking threading configuration
            
        Returns:
            Processed dictionary with normalized session IDs
        """
        result = data.copy()
        
        for key, value in result.items():
            # If key is session_id, normalize it
            if key == "session_id" and isinstance(value, str):
                result[key] = PayloadService.normalize_session_id(value, client)
            # If value is another dictionary, recursively process it
            elif isinstance(value, dict):
                result[key] = PayloadService._process_dict_recursively(value, client)
            # If value is a list, check each item for dictionaries
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, dict):
                        new_list.append(PayloadService._process_dict_recursively(item, client))
                    else:
                        new_list.append(item)
                result[key] = new_list
        
        return result
    
    @staticmethod
    def prepare_event_data(data: Dict[str, Any], session_id: Optional[str] = None, client=None) -> Dict[str, Any]:
        """
        Prepare event data, ensuring session IDs are normalized appropriately for events
        Recursively processes nested dictionaries to find and normalize all session_id fields

        Args:
            data: The original event data dictionary
            session_id: Optional session ID to include in data if not already present
            client: Optional client object for checking threading configuration

        Returns:
            Updated event data with normalized session ID if applicable
        """
        event_data = data.copy() if data else {}

        # If session_id provided and not in data, add it
        if session_id and "session_id" not in event_data:
            event_data["session_id"] = session_id

        # Process entire dictionary tree recursively
        return PayloadService._process_dict_recursively(event_data, client)

    @staticmethod
    def create_payload(entity_id: str, entity_type: EntityType) -> Tuple:
        strategies = {
            EntityType.CHAT_MESSAGE: MessagePayloadStrategy(),
            EntityType.CHAT_SUGGESTION: SuggestionPayloadStrategy(),
        }
        strategy = strategies[entity_type]

        # Get message based on strategy type
        entity = strategy.get_entity(entity_id=entity_id)
        session = strategy.get_session(entity=entity)
        payload = strategy.create_payload(entity=entity)

        return payload
