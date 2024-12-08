from mongoengine import DoesNotExist, ValidationError
from fastapi import HTTPException

from app.models.mongodb.client import Client
from app.models.mongodb.client_channel import ClientChannel
from app.schemas.client import ClientChannelCreateorUpdateRequest, ClientChannelResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ClientChannelService:
    @staticmethod
    def create_channel(client_id: str, request: ClientChannelCreateorUpdateRequest) -> ClientChannelResponse:
        """
        Creates a new client channel.
        """
        try:
            client = Client.objects.get(client_id=client_id)
            channel = ClientChannel(
                channel_type=request.channel_type.value,
                channel_config=request.channel_config.model_dump(),
                client=client,
                is_active=request.is_active,
            )
            channel.save()
            return ClientChannelResponse.model_validate(channel.to_serializable_dict())
        except DoesNotExist:
            raise HTTPException(404, "Client not found")
        except ValidationError as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            raise HTTPException(400, f"Invalid input: {e}")

    @staticmethod
    def list_channels(client_id: str) -> list[ClientChannelResponse]:
        """
        Retrieves a list of all channels for a specific client.
        """
        try:
            client = Client.objects.get(client_id=client_id)
            channels = ClientChannel.objects(client=client, is_active=True).all()
            return [ClientChannelResponse.model_validate(channel.to_serializable_dict()) for channel in channels]
        except DoesNotExist:
            raise HTTPException(404, "Client not found")

    @staticmethod
    def update_channel(client_id: str, channel_id: str, request: ClientChannelCreateorUpdateRequest) -> dict:
        """
        Updates an existing client channel.
        """
        try:
            channel = ClientChannel.objects.get(id=channel_id)
            channel.update(**request.model_dump(exclude_unset=True))
            return {"message": "Channel updated successfully"}
        except DoesNotExist:
            raise HTTPException(404, "Client not found")

    @staticmethod
    def get_channel_by_type(client_id: str, channel_type: str) -> ClientChannel:
        """
        Retrieves a specific channel for a client by its type.
        """
        try:
            client = Client.objects.get(client_id=client_id)
            channel = ClientChannel.objects.get(client=client, channel_type=channel_type)
            return channel
        except DoesNotExist:
            raise HTTPException(404, "Client not found")

    @staticmethod
    def get_channel_webhook_url(client_id: str, channel_id: str) -> str:
        """
        Retrieves the webhook URL for a specific channel.
        """
        try:
            channel = ClientChannel.objects.get(id=channel_id)
            channel_response = ClientChannelResponse.model_validate(channel.to_serializable_dict())
            return channel_response.channel_config.webhook_url
        except DoesNotExist:
            raise HTTPException(404, "Channel not found")
