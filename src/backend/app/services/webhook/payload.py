from typing import Tuple

from app.models.mongodb.channel_request_log import EntityType
from .message_payload import MessagePayloadStrategy
from .suggestion_payload import SuggestionPayloadStrategy


class PayloadService:
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
