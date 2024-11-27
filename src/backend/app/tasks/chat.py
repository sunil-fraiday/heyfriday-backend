import requests
from requests import Response
import traceback

from celery import shared_task
from celery.utils.log import get_task_logger

import app.constants as constants
from app.core.config import settings
from app.db.mongodb_utils import connect_to_db, disconnect_from_db
from app.schemas.chat import ChatMessageResponse
from app.models.mongodb.chat_message import ChatMessage, SenderType
from app.services.message_processor import MessageProcessor


logger = get_task_logger(__name__)

connect_to_db()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    soft_time_limit=300,
    time_limit=360,
)
def process_chat_message(self, message_id: str):
    try:

        chat_message: ChatMessage = ChatMessage.objects.get(id=message_id)
        message_data = chat_message.text

        processor = MessageProcessor()
        processed_message = processor.get_response(message_data)

        ai_message = ChatMessage(
            session=chat_message.session,
            sender=constants.BOT_SENDER_NAME,
            sender_name=constants.BOT_SENDER_NAME,
            sender_type=SenderType.BOT,
            text=processed_message.data.answer.answer_text,
            sql_data={"sql_data": processed_message.data.answer.answer_data},
        )
        ai_message.save()

        logger.info(f"Processed message: {chat_message.id}")
        
        payload = ChatMessageResponse.from_chat_message(ai_message).model_dump(mode="json")
        logger.info(f"Payload: {payload}")
        response: Response = requests.post(
            settings.SWYT_WEBHOOK_URL, json=payload
        )
        response.raise_for_status()

    except Exception as exc:
        logger.error(f"Message processing failed: {exc}, \n Traceback: {traceback.format_exc()}")
        self.retry(exc=exc)
