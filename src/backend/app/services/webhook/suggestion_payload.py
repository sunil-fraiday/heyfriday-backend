from typing import Dict

from app.models.mongodb.chat_message_suggestion import ChatMessageSuggestion
from app.models.mongodb.channel_request_log import EntityType
from .base import WebhookPayloadStrategy


class SuggestionPayloadStrategy(WebhookPayloadStrategy):
    def create_payload(self, entity: "ChatMessageSuggestion") -> Dict:
        return {
            "id": str(entity.id),
            "chat_session_id": str(entity.chat_session.id),
            "original_message_id": str(entity.chat_message.id),
            "text": entity.text,
            "attachments": ([att.to_mongo().to_dict() for att in entity.attachments] if entity.attachments else []),
            "data": entity.data,
            "created_at": entity.created_at.isoformat(),
            "type": EntityType.CHAT_SUGGESTION.value,
        }

    def get_entity(self, entity_id: str) -> ChatMessageSuggestion:
        return ChatMessageSuggestion.objects.get(id=entity_id)

    def handle_response(self, entity: "ChatMessageSuggestion", response_data: Dict) -> None:
        if response_data and "id" in response_data:
            entity.external_id = response_data["id"]
            entity.save()

    def get_session(self, entity: "ChatMessageSuggestion"):
        return entity.chat_session

    def get_message_id(self, message: "ChatMessageSuggestion") -> str:
        return str(message.id)
