from typing import Dict

from app.models.mongodb.chat_message import ChatMessage
from app.schemas.chat import ChatMessageResponse
from app.models.mongodb.channel_request_log import EntityType
from .base import WebhookPayloadStrategy


class MessagePayloadStrategy(WebhookPayloadStrategy):
    def create_payload(self, entity: "ChatMessage") -> Dict:
        payload = ChatMessageResponse.from_chat_message(entity).model_dump(mode="json")
        payload["type"] = EntityType.CHAT_MESSAGE.value
        return payload

    def handle_response(self, entity: "ChatMessage", response_data: Dict) -> None:
        if response_data and "id" in response_data:
            entity.external_id = response_data["id"]
            entity.save()

    def get_session(self, entity: "ChatMessage"):
        return entity.session

    def get_message_id(self, message: "ChatMessage") -> str:
        return str(message.id)

    def get_entity(self, entity_id: str) -> ChatMessage:
        return ChatMessage.objects.get(id=entity_id)
