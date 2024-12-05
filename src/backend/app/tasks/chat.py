import requests
from requests import Response
from requests.exceptions import RequestException
import traceback

from celery import shared_task, chain
from celery.utils.log import get_task_logger

import app.constants as constants
from app.core.config import settings
from app.db.mongodb_utils import connect_to_db
from app.schemas.chat import ChatMessageResponse
from app.models.mongodb.chat_message import ChatMessage, SenderType, MessageCategory
from app.models.mongodb.chat_session import ChatSession
from app.services.ai_service import AIService
from app.services.intent_classification import IntentClassificationService
from app.services.chat.utils import create_system_chat_message
from app.services.chat.message import ChatMessageService

logger = get_task_logger(__name__)

connect_to_db()


INTENT_CLASSIFICATION_ERROR_MESSAGE = """
🚨 Oops! We are not able to understand your intent for the given message. Please try rephrasing the message and try again.
"""

AI_SERVICE_ERROR_MESSAGE = """
🤖 We're sorry!
We couldn't generate a response to your message.
Please try rephrasing your message and try again.
"""

WEBHOOK_ERROR_MESSAGE = """
📡 Delivery Failed!
Your message was processed, but we couldn't respond.
We'll retry shortly, or you can contact support if this persists.
"""


@shared_task(bind=True)
def identify_intent_task(self, message_id: str):
    """
    First task: Handles intent classification and authorization.
    """
    try:
        chat_message = ChatMessage.objects.get(id=message_id)
        message_data = chat_message.text
        logger.info(f"Message: {message_data}")
        intent_service = IntentClassificationService(
            aws_runtime=settings.AWS_BEDROCK_RUNTIME,
            region_name=settings.AWS_BEDROCK_REGION,
            access_key_id=settings.AWS_BEDROCK_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_BEDROCK_SECRET_ACCESS_KEY,
            model_name="mistral.mistral-large-2402-v1:0",
        )
        intent = intent_service.classify_with_bedrock(
            current_message=message_data,
            chat_history=ChatMessageService.list_messages(
                session_id=chat_message.session.session_id, last_n=6, exclude_id=[message_id]
            ),
            resource_scope_mapping={},
        )
        logger.info(f"Intent: {intent}")
        # Pass session and message data to the next task
        return {
            "session_id": str(chat_message.session.id),
            "message_id": str(chat_message.id),
            "intent": intent,  # Pass the intent to the next task
        }

    except Exception as exc:
        session = ChatMessage.objects.get(id=message_id).session
        message = create_system_chat_message(
            session=session,
            error_message=INTENT_CLASSIFICATION_ERROR_MESSAGE,
            message_category=MessageCategory.ERROR,
        )
        send_to_webhook_task.delay(message_data={"message_id": str(message.id)})
        raise exc  # Stop the chain if there is an exception here


@shared_task(bind=True)
def generate_ai_response_task(self, session_data: dict):
    try:
        logger.info(f"Session data: {session_data}")
        message_id = session_data["message_id"]
        message = ChatMessage.objects.get(id=message_id)

        processor = AIService()
        processed_message = processor.get_response(message_id=message_id)

        ai_message = ChatMessage(
            session=message.session,
            sender=constants.BOT_SENDER_NAME,
            sender_name=constants.BOT_SENDER_NAME,
            sender_type=SenderType.ASSISTANT,
            text=processed_message.data.answer.answer_text,
            data={"sql_data": processed_message.data.answer.answer_data},
        )
        ai_message.save()

        # Pass message ID to the next task
        return {"message_id": str(ai_message.id), "session_id": str(message.session.id)}

    except Exception as exc:
        # Send system error message
        session = ChatSession.objects.get(id=session_data["session_id"])
        message = create_system_chat_message(
            session=session,
            error_message=AI_SERVICE_ERROR_MESSAGE,
            message_category=MessageCategory.ERROR,
        )
        send_to_webhook_task.delay(message_data={"message_id": str(message.id)})
        raise exc  # Stop the chain


@shared_task(bind=True, max_retries=3)
def send_to_webhook_task(self, message_data: dict):
    try:
        logger.info(f"Session data: {message_data}")

        message_id = message_data["message_id"]
        message = ChatMessage.objects.get(id=message_id)

        payload = ChatMessageResponse.from_chat_message(message).model_dump(mode="json")
        response = requests.post(settings.SWYT_WEBHOOK_URL, json=payload)
        response.raise_for_status()

    except RequestException as exc:
        logger.error(f"Webhook notification failed: {exc}")
        raise self.retry(exc=exc, countdown=60)  # Retry after 60 seconds

    except Exception as exc:
        # Send system error message if retries fail
        session = ChatMessage.objects.get(id=message_data["message_id"]).session
        message_id = create_system_chat_message(
            session=session,
            error_message=WEBHOOK_ERROR_MESSAGE,
            message_category=MessageCategory.ERROR,
        )
        send_to_webhook_task.delay(message_data={"message_id": str(message_id)})
        raise exc  # Stop the chain


def trigger_chat_workflow(message_id: str):
    """
    Starts the message processing chain.
    """
    process_chain = chain(
        identify_intent_task.s(message_id),  # First task
        generate_ai_response_task.s(),  # Second task
        send_to_webhook_task.s(),  # Third task
    )
    process_chain.apply_async()
