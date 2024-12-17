import re
import requests
import traceback
import logging
import json
from datetime import timedelta

from app.core.config import settings
from app.schemas.ai_response import AIResponse, AIServiceRequest
from app.utils.logger import get_logger
from app.exceptions import AIProcessingException

logger = get_logger(__name__)


class AIService:

    def get_response(self, message_id: str) -> AIResponse:
        try:
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

    def prepare_payload(self, message_id: str):
        from app.services.chat.message import ChatMessageService

        try:
            chat_message = ChatMessageService.get_message(message_id=message_id)
            chat_message_history = ChatMessageService.list_messages(
                last_n=6,
                exclude_id=[message_id],
                session_id=chat_message.session_id,
                start_date=chat_message.created_at - timedelta(minutes=10), # Get messages only from past 10 minutes
            )[::-1]
            return AIServiceRequest(
                current_message=chat_message.text,
                chat_history=chat_message_history,
                session_id=chat_message.session_id,
                sender_id=chat_message.sender_id,
                sender_type=chat_message.sender_type,
                created_at=chat_message.created_at,
                updated_at=chat_message.updated_at,
            )
        except Exception as e:
            logger.error(f"Error creating AI Service Request: {str(e)}", exc_info=True)
            raise AIProcessingException(f"Error creating AI Service Request: {str(e)}")
