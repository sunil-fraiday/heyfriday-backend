import uuid
import string
import secrets
from fastapi import HTTPException
from mongoengine import DoesNotExist, NotUniqueError
from pydantic import ValidationError

from app.models.mongodb.client import Client
from app.models.mongodb.chat_message import ChatMessage
from app.schemas.client import ClientCreateorUpdateRequest, ClientResponse


def generate_client_secret(length=32):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(alphabet) for _ in range(length))


class ClientService:
    @staticmethod
    def create_client(request: ClientCreateorUpdateRequest) -> ClientResponse:
        """
        Creates a new client.
        """
        try:
            client = Client(
                name=request.name,
                email=request.email,
                client_id=request.client_id or str(uuid.uuid4()),
                client_key=generate_client_secret(),
                is_active=request.is_active,
            )
            client.save()
            return ClientResponse.model_validate_json(client.to_serializable_dict())
        except NotUniqueError as e:
            raise HTTPException(400, f"Duplicate field: {str(e)}")
        except ValidationError as e:
            raise HTTPException(400, f"Invalid input: {e.json()}")

    @staticmethod
    def get_client(client_id: str) -> ClientResponse:
        """
        Retrieves a client by its ID.
        """
        try:
            client = Client.objects.get(client_id=client_id)
            return client
        except DoesNotExist:
            raise HTTPException(404, f"Client with ID {client_id} not found")

    @staticmethod
    def list_clients() -> list[ClientResponse]:
        """
        Retrieves a list of all clients.
        """
        clients = Client.objects(is_active=True).all()
        return [ClientResponse.model_validate(client.to_serializable_dict()) for client in clients]

    @staticmethod
    def update_client(client_id: str, request: ClientCreateorUpdateRequest) -> dict:
        """
        Updates an existing client.
        """
        try:
            client = Client.objects.get(client_id=client_id)
            client.update(**request.model_dump(exclude_unset=True))
            return ClientResponse.model_validate(client.to_serializable_dict())
        except DoesNotExist:
            raise HTTPException(status_code=404, deftail="Client not found")
