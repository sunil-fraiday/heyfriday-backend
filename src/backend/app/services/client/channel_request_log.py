from mongoengine import DoesNotExist
from datetime import datetime
from datetime import timezone
import logging
from typing import Union, Optional, Dict, Tuple

from app.models.mongodb.chat_message import ChatMessage
from app.models.mongodb.chat_message_suggestion import ChatMessageSuggestion
from app.models.mongodb.client_channel import ClientChannel
from app.models.mongodb.channel_request_log import ChannelRequestLog, ChannelRequestLogStatus, EntityType
from app.models.mongodb.channel_request_log_attempt import ChannelRequestLogAttempt, ChannelRequestLogAttemptStatus

logger = logging.getLogger(__name__)


class ChannelRequestLogService:
    @staticmethod
    def get_or_create(
        entity: Union[ChatMessage, ChatMessageSuggestion],
        channel: ClientChannel,
        request_payload: Optional[Dict] = None,
    ) -> Tuple[ChannelRequestLog, bool]:
        """Get or create a channel request log"""

        # Determine entity type and request type based on instance
        entity_type = (
            EntityType.CHAT_SUGGESTION.value
            if isinstance(entity, ChatMessageSuggestion)
            else EntityType.CHAT_MESSAGE.value
        )

        try:
            # Try to get existing log
            log = ChannelRequestLog.objects.get(
                entity_id=str(entity.id), entity_type=entity_type, client_channel=channel
            )
            created = False
        except ChannelRequestLog.DoesNotExist:
            # Create new log
            log = ChannelRequestLog(
                entity_id=str(entity.id),
                entity_type=entity_type,
                client_channel=channel,
                request_payload=request_payload,
            )
            log.save()
            created = True

        return log, created

    @staticmethod
    def get_entity(log: ChannelRequestLog) -> Union[ChatMessage, ChatMessageSuggestion, None]:
        """Get the entity associated with the log"""
        entity_map = {
            EntityType.CHAT_MESSAGE.value: ChatMessage,
            EntityType.CHAT_SUGGESTION.value: ChatMessageSuggestion,
        }

        model_class = entity_map.get(log.entity_type)
        if not model_class:
            return None

        try:
            return model_class.objects.get(id=log.entity_id)
        except model_class.DoesNotExist:
            return None

    @staticmethod
    def log_attempt(
        request_log: ChannelRequestLog,
        attempt_number,
        success,
        response_status=None,
        response_body=None,
        error_message=None,
    ):
        """
        Log an attempt for the given ChannelRequestLog.
        """
        attempt = ChannelRequestLogAttempt(
            channel_request_log=request_log,
            attempt_number=attempt_number,
            response_status=response_status,
            response_body=response_body,
            error_message=error_message,
            status=(
                ChannelRequestLogAttemptStatus.SUCCESS.value
                if success
                else ChannelRequestLogAttemptStatus.FAILURE.value
            ),
            attempted_at=datetime.now(timezone.utc),
        )
        attempt.save()

        if success:
            request_log.status = ChannelRequestLogStatus.SUCCESS.value
        elif attempt_number >= request_log.max_attempts:
            request_log.status = ChannelRequestLogStatus.FAILURE.value
        request_log.updated_at = datetime.now(timezone.utc)
        request_log.save()

        return attempt

    @staticmethod
    def update_log_status(request_log, status):
        """
        Update the status of the ChannelRequestLog.
        """
        request_log.status = status
        request_log.updated_at = datetime.now(timezone.utc)
        request_log.save()
