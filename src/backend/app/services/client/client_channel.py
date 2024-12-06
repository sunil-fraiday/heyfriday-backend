from mongoengine import DoesNotExist, ValidationError
from fastapi import HTTPException

from app.models.mongodb.client import Client
from app.models.mongodb.client_channel import ClientChannel
from app.schemas.client import ClientChannelCreateorUpdateRequest, ClientChannelResponse


class ClientChannelService:
    @staticmethod
    def create_channel(request: ClientChannelCreateorUpdateRequest) -> ClientChannelResponse:
        """
        Creates a new client channel.
        """
        try:
            client = Client.objects.get(client_id=request.client_id)
            channel = ClientChannel(
                channel_type=request.channel_type.value,
                channel_config=request.channel_config,
                client=client,
                is_active=request.is_active,
            )
            channel.save()
            return ClientChannelResponse.model_validate(channel.to_mongo().to_dict())
        except DoesNotExist:
            raise HTTPException(404, "Client not found")
        except ValidationError as e:
            raise HTTPException(400, f"Invalid input: {e.json()}")

    @staticmethod
    def list_channels(client_id: str) -> list[ClientChannelResponse]:
        """
        Retrieves a list of all channels for a specific client.
        """
        try:
            client = Client.objects.get(client_id=client_id)
            channels = ClientChannel.objects(client=client, is_active=True).all()
            return [ClientChannelResponse.model_validate(channel.to_mongo().to_dict()) for channel in channels]
        except DoesNotExist:
            raise HTTPException(404, "Client not found")

    @staticmethod
    def update_channel(channel_id: str, request: ClientChannelCreateorUpdateRequest) -> dict:
        """
        Updates an existing client channel.
        """
        try:
            channel = ClientChannel.objects.get(id=channel_id)
            channel.update(**request.model_dump(exclude_unset=True))
            return {"message": "Channel updated successfully"}
        except DoesNotExist:
            raise HTTPException(404, "Client not found")
