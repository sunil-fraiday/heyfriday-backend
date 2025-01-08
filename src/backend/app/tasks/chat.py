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
from app.models.mongodb.client import KeycloakConfig
from app.models.mongodb.channel_request_log import ChannelRequestLog
from app.services.ai_service import AIService
from app.services.analysis import MessageAnalysisService
from app.services.chat.utils import create_system_chat_message
from app.services.chat.message import ChatMessageService
from app.services.client import ChannelRequestLogService, ClientChannelService
from app.services.keycloak import KeycloakAuthorizationService

logger = get_task_logger(__name__)

connect_to_db()


INTENT_CLASSIFICATION_ERROR_MESSAGE = """
🚨 Oops! We are not able to understand your intent for the given message. Please try rephrasing the message and try again.
"""

UNAUTHORIZED_MESSAGE = """
🚨 Oops! You are not authorized to ask for this specific information.
"""

AUTHORIZATION_ERROR_MESSAGE = """
🤖 We're sorry!
We couldn't authorize your request.
If this issue persists, please contact support.
"""

AI_SERVICE_ERROR_MESSAGE = """
🤖 We're sorry!
We couldn't generate a response to your message.
Please try rephrasing your message and try again.
"""

CATEGORY_ERROR_MESSAGE = """
I understand your query requires specific expertise. I'm connecting you
with one of our support specialists who will be able to assist you further.
A team member will be with you shortly.
"""

WEBHOOK_ERROR_MESSAGE = """
📡 Delivery Failed!
Your message was processed, but we couldn't respond.
We'll retry shortly, or you can contact support if this persists.
"""

ALLOWED_CATEGORIES = ["general_inquiry", "general_troubleshooting"]


@shared_task(bind=True)
def identify_intent_task(self, message_id: str):
    """
    First task: Handles intent classification and authorization.
    """
    try:
        chat_message = ChatMessage.objects.get(id=message_id)
        message_data = chat_message.text
        logger.info(f"Message: {message_data}")
        analysis_service = MessageAnalysisService(
            aws_runtime=settings.AWS_BEDROCK_RUNTIME,
            region_name=settings.AWS_BEDROCK_REGION,
            access_key_id=settings.AWS_BEDROCK_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_BEDROCK_SECRET_ACCESS_KEY,
            model_name="mistral.mistral-large-2402-v1:0",
        )
        intent = analysis_service.analyse_category(
            current_message=chat_message,
            chat_history=ChatMessageService.list_messages(
                session_id=chat_message.session.session_id, last_n=30, exclude_id=[message_id]
            ),
        )
        logger.info(f"Category: {intent}")
        category = intent.get("category")
        if category in ALLOWED_CATEGORIES:
            # Pass session and message data to the next task
            return {
                "session_id": str(chat_message.session.id),
                "message_id": str(chat_message.id),
                "intent": intent,  # Pass the intent to the next task
            }
        else:
            session = ChatMessage.objects.get(id=message_id).session
            message = create_system_chat_message(
                session=session,
                error_message=CATEGORY_ERROR_MESSAGE,
                message_category=MessageCategory.INFO,
            )
            send_to_webhook_task.delay(message_data={"message_id": str(message.id)})
            if self.request.chain:  # Stop the chain if not in allowed categories
                self.request.chain[:] = []

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
def authorization(self, session_data: dict):
    logger.info(f"Session data: {session_data}")
    message_id = session_data["message_id"]
    try:
        message: ChatMessage = ChatMessage.objects.get(id=message_id)
        session: ChatSession = message.session
        client = session.client
        keycloak_config: KeycloakConfig = client.get_keycloak_config()

        if not keycloak_config:  # Continue without authorization flow if keycloak config is not available
            return session_data

        intent = session_data["intent"]
        resource = intent.get("Resource", None)
        scopes = intent.get("Scopes", [])
        scope = scopes[0] if scopes else None
        logger.info(f"Resource: {resource}, Scope: {scope}")

        keycloak_service = KeycloakAuthorizationService(
            server_url=keycloak_config.server_url,
            realm=keycloak_config.realm,
            client_id=keycloak_config.client_id,
            client_secret=keycloak_config.client_secret,
        )
        admin_token = keycloak_service.get_admin_access_token(
            keycloak_config.admin_username, keycloak_config.admin_password
        )

        # Perform the token exchange
        exchanged_token = keycloak_service.exchange_token(admin_token, message.sender)
        print("Exchanged Token:", exchanged_token)

        if resource and scope:
            is_authorized = keycloak_service.validate_user_authorization(
                exchanged_token["access_token"], resource, scope
            )

            if is_authorized:
                logger.info(f"User is authorized to access {resource} with scope {scope}.")
                return session_data
            else:
                logger.info(f"User is NOT authorized to access {resource} with scope {scope}.")
                message = create_system_chat_message(
                    session=session,
                    error_message=UNAUTHORIZED_MESSAGE,
                    message_category=MessageCategory.INFO,
                )
                send_to_webhook_task.delay(message_data={"message_id": str(message.id)})
                if self.request.chain:  # Stop the chain if not in allowed categories
                    self.request.chain[:] = []

        logger.info("Resource or Scope was not identified from the Intent classifier so skipping authorization.")
    except Exception as exc:
        # Send system error message
        session = ChatSession.objects.get(id=session_data["session_id"])
        message = create_system_chat_message(
            session=session,
            error_message=AUTHORIZATION_ERROR_MESSAGE,
            message_category=MessageCategory.ERROR,
        )
        send_to_webhook_task.delay(message_data={"message_id": str(message.id)})
        raise exc


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
        message: ChatMessage = ChatMessage.objects.get(id=message_id)

        # Get or create the ChannelRequestLog
        request_log, created = ChannelRequestLogService.get_or_create(
            chat_message=message,
            channel=message.session.client_channel,
        )
        payload = ChatMessageResponse.from_chat_message(message).model_dump(mode="json")
        webhook_url = ClientChannelService.get_channel_webhook_url(
            client_id=message.session.client.id,
            channel_id=message.session.client_channel.id,
        )

        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()

        response_data = response.json()
        if response_data and "id" in response_data:
            message.external_id = response_data["id"]
            message.save()

        # Log the successful attempt
        ChannelRequestLogService.log_attempt(
            request_log=request_log,
            attempt_number=self.request.retries + 1,
            success=True,
            response_status=response.status_code,
            response_body=response.json(),
        )

    except RequestException as exc:
        logger.error(f"Webhook notification failed: {exc}")

        # Log the failed attempt
        request_log = ChannelRequestLog.objects.get(chat_message=message_id)  # Ensure we fetch the log
        ChannelRequestLogService.log_attempt(
            request_log=request_log,
            attempt_number=self.request.retries + 1,
            success=False,
            error_message=str(exc),
        )
        raise self.retry(exc=exc, countdown=60)  # Retry after 60 seconds

    except Exception as exc:
        logger.error(f"Unexpected error: {exc}")
        # Send system error message if retries fail
        session = ChatMessage.objects.get(id=message_id).session
        system_message = create_system_chat_message(
            session=session,
            error_message=WEBHOOK_ERROR_MESSAGE,
            message_category=MessageCategory.ERROR,
        )
        send_to_webhook_task.delay(message_data={"message_id": str(system_message.id)})
        raise exc  # Stop the chain


def trigger_chat_workflow(message_id: str):
    """
    Starts the message processing chain.
    """
    process_chain = chain(
        identify_intent_task.s(message_id),  # First task
        authorization.s(),  # Second task
        generate_ai_response_task.s(),  # Third task
        send_to_webhook_task.s(),  # Fourth task
    )
    process_chain.apply_async()
