from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from app.services.client.structured_data_store import ClientStructuredDataStoreService
from app.models.mongodb.utils import CredentialManager
from app.models.mongodb.client_structured_data_store import ClientStructuredDataStore
from app.schemas.client.structured_data_store import ClientStructuredDataStoreResponse
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/clients/{client_id}/data-stores", tags=["database"])


class DatabaseConfigResponse(BaseModel):
    database_type: str
    host: str
    port: int
    database: str
    user: str
    password: str


async def verify_api_key(authorization: Optional[str] = Header(None)):
    """Verify API key from headers"""
    if not authorization:
        raise HTTPException(status_code=403, detail="Missing API key")

    x_api_key = authorization.split(" ")[1]
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


@router.get("/{data_store_id}/credentials", response_model=DatabaseConfigResponse)
async def get_database_config(client_id: str, data_store_id: str, api_key: Optional[str] = Depends(verify_api_key)):
    """
    Get database configuration for a client
    """
    try:
        credential_manager = CredentialManager(current_key=settings.ENCRYPTION_KEY)
        store_service = ClientStructuredDataStoreService(credential_manager=credential_manager)
        data_store: ClientStructuredDataStore = store_service.get_data_store(
            client_id=client_id, data_store_id=data_store_id
        )
        config = data_store.get_config(credential_manager)

        return DatabaseConfigResponse(
            database_type=data_store.database_type,
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password,
        )

    except Exception as e:
        logger.error(f"Error fetching database config for client {client_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ClientStructuredDataStoreResponse])
async def get_database_config(client_id: str):
    """"""
    try:
        credential_manager = CredentialManager(current_key=settings.ENCRYPTION_KEY)
        store_service = ClientStructuredDataStoreService(credential_manager=credential_manager)
        data_stores: List[ClientStructuredDataStore] = store_service.list_data_stores(client_id=client_id)
        return [
            ClientStructuredDataStoreResponse(
                id=str(data_store.id), database_type=data_store.database_type, is_active=data_store.is_active
            )
            for data_store in data_stores
        ]
    except Exception as e:
        logger.error(f"Error fetching database config for client {client_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
