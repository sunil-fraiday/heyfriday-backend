from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from app.services.client.structured_data_store import ClientStructuredDataStoreService
from app.models.mongodb.utils import CredentialManager
from app.models.mongodb.client_structured_data_store import ClientStructuredDataStore
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/clients/{client_id}/data-stores", tags=["database"])


class DatabaseConfigResponse(BaseModel):
    database_type: str
    host: str
    port: int
    database: str
    username: str
    password: str
    additional_params: dict = {}


async def verify_api_key(authorization: str = Header(...)):
    """Verify API key from headers"""
    x_api_key = authorization.split(" ")[1]
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


@router.get("/credentials", response_model=DatabaseConfigResponse)
async def get_database_config(client_id: str, api_key: str = Depends(verify_api_key)):
    """
    Get database configuration for a client
    """
    try:
        credential_manager = CredentialManager(current_key=settings.ENCRYPTION_KEY)
        store_service = ClientStructuredDataStoreService(credential_manager=credential_manager)
        data_store: ClientStructuredDataStore = store_service.get_data_store(client_id=client_id)
        config = data_store.get_config(credential_manager)

        return DatabaseConfigResponse(
            database_type=data_store.database_type,
            host=config.host,
            port=config.port,
            database=config.database,
            username=config.username,
            password=config.password,
            additional_params=config.additional_params,
        )

    except Exception as e:
        logger.error(f"Error fetching database config for client {client_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
