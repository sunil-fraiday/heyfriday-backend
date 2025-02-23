import re
import requests
import traceback
import logging
import json
from datetime import timedelta

from app.core.config import settings
from app.schemas.ai_response import AIResponse, AIServiceRequest, Data, Answer
from app.models.mongodb.client_channel import ChannelType, ClientChannel
from app.utils.logger import get_logger
from app.exceptions import AIProcessingException

logger = get_logger(__name__)


class AIService:

    def get_response(self, message_id: str) -> AIResponse:
        try:
            chat_message = self._get_chat_message(message_id=message_id)
            client_channel: ClientChannel = chat_message.session.client_channel

            if client_channel.channel_type == ChannelType.SLACK.value:
                response = requests.post(
                    settings.SLACK_AI_SERVICE_URL,
                    json={
                        "id": "67b6fa6f3a4e46f5455999c7",
                        "input_args": {
                            "client_id": "4rZvgHUh8PShgsy",
                            "data_store_id": "67b57cf0abb6a2d5a8ac5327",
                            "human_msg": chat_message.text,
                            "session_id": str(chat_message.session.session_id),
                        },
                    },
                    headers={"Authorization": f"Basic {settings.SLACK_AI_TOKEN}"},
                )
                ai_response = response.json()
                return AIResponse(
                    status=ai_response["status"],
                    message="",
                    data=Data(
                        answer=Answer(answer_data={}, answer_url="www.example.com", answer_text=ai_response["result"])
                    ),
                )
            else:
                response = requests.post(
                    settings.AI_SERVICE_URL,
                    json=json.loads(
                        self.prepare_payload(message_id).model_dump_json()
                    ),  # Prevent double jsonification of the payload
                )
                ai_response = response.json()
                logger.info(f"AI Response: {ai_response}")
                return AIResponse(**ai_response)
        except Exception as e:
            logging.error(f"Error in ai service: {str(e)}")
            logging.error(traceback.format_exc())
            raise Exception("Error in AI Service")

    def _get_chat_message(self, message_id: str):
        from app.services.chat.message import ChatMessageService

        chat_message = ChatMessageService.get_message(message_id=message_id)
        return chat_message

    def prepare_payload(self, message_id: str):
        from app.services.chat.message import ChatMessageService

        try:
            chat_message = ChatMessageService.get_message(message_id=message_id)
            chat_message_history = ChatMessageService.list_messages(
                last_n=100,
                exclude_id=[message_id],
                session_id=chat_message.session.session_id,
            )[::-1]
            return AIServiceRequest(
                current_message=chat_message.text,
                chat_history=chat_message_history,
                session_id=chat_message.session.session_id,
                sender_id=chat_message.sender,
                sender_type=chat_message.sender_type,
                created_at=chat_message.created_at,
                updated_at=chat_message.updated_at,
                current_message_id=str(chat_message.id),
            )
        except Exception as e:
            logger.error(f"Error creating AI Service Request: {str(e)}", exc_info=True)
            raise AIProcessingException(f"Error creating AI Service Request: {str(e)}")
