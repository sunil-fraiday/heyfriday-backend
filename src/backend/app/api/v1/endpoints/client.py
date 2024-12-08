from fastapi import APIRouter, HTTPException
from typing import List

from app.services.client import ClientService
from app.schemas.client import ClientCreateorUpdateRequest, ClientResponse

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("", response_model=ClientResponse)
def create_client(request: ClientCreateorUpdateRequest):
    try:
        return ClientService.create_client(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[ClientResponse])
def list_clients():
    return ClientService.list_clients()


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(client_id: str, request: ClientCreateorUpdateRequest):
    try:
        return ClientService.update_client(client_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
