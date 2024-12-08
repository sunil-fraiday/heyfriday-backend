from mongoengine import DoesNotExist
from datetime import datetime
from datetime import timezone
import logging

from app.models.mongodb.channel_request_log import ChannelRequestLog, ChannelRequestLogStatus
from app.models.mongodb.channel_request_log_attempt import ChannelRequestLogAttempt, ChannelRequestLogAttemptStatus

logger = logging.getLogger(__name__)


class ChannelRequestLogService:
    @staticmethod
    def get_or_create(chat_message_id, channel):
        """
        Get or create a ChannelRequestLog for the given chat_message_id and channel.
        """
        try:
            log = ChannelRequestLog.objects.get(message=chat_message_id, channel=channel)
            return log, False  # False indicates it was not created
        except DoesNotExist:
            log = ChannelRequestLog(
                message=chat_message_id,
                channel=channel,
                request_payload={},
                request_headers={},
                max_attempts=3,
                status=ChannelRequestLogStatus.PENDING,
            )
            log.save()
            return log, True  # True indicates it was created

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
            request_log=request_log,
            attempt_number=attempt_number,
            response_status=response_status,
            response_body=response_body,
            error_message=error_message,
            status=ChannelRequestLogAttemptStatus.SUCCESS if success else ChannelRequestLogAttemptStatus.FAILURE,
            attempt_at=datetime.now(timezone.utc),
        )
        attempt.save()

        if success:
            request_log.status = "Success"
        elif attempt_number >= request_log.max_attempts:
            request_log.status = "Failure"
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
