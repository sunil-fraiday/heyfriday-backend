from mongoengine import DoesNotExist, NotUniqueError
from pydantic import ValidationError

from app.models.mongodb.client import Client
from schemas import ClientCreateRequest, ClientUpdateRequest, ClientResponse


class ClientService:
    @staticmethod
    def create_client(request: ClientCreateRequest) -> ClientResponse:
        """
        Creates a new client.
        """
        try:
            client = Client(
                name=request.name,
                email=request.email,
                client_id=request.client_id,
                client_key=request.client_key,
                keycloak_config=request.keycloak_config,
                is_active=request.is_active,
            )
            client.save()
            return ClientResponse.parse_obj(client.to_mongo().to_dict())
        except NotUniqueError as e:
            raise ValueError(f"Duplicate field: {str(e)}")
        except ValidationError as e:
            raise ValueError(f"Invalid input: {e.json()}")

    @staticmethod
    def list_clients() -> list[ClientResponse]:
        """
        Retrieves a list of all clients.
        """
        clients = Client.objects(is_active=True).all()
        return [ClientResponse.parse_obj(client.to_mongo().to_dict()) for client in clients]

    @staticmethod
    def update_client(client_id: str, request: ClientUpdateRequest) -> dict:
        """
        Updates an existing client.
        """
        try:
            client = Client.objects.get(client_id=client_id)
            client.update(**request.dict(exclude_unset=True))
            return {"message": "Client updated successfully"}
        except DoesNotExist:
            raise ValueError("Client not found")
