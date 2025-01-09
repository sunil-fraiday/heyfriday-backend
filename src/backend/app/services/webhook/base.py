from abc import ABC, abstractmethod
from typing import Dict, Any


class WebhookPayloadStrategy(ABC):
    @abstractmethod
    def create_payload(self, entity: Any) -> Dict:
        pass

    @abstractmethod
    def handle_response(self, entity: Any, response_data: Dict) -> None:
        pass

    @abstractmethod
    def get_session(self, entity: Any) -> Any:
        pass

    @abstractmethod
    def get_message_id(self, message: Any) -> str:
        pass

    @abstractmethod
    def get_entity(self, entity_id: str) -> Any:
        pass
