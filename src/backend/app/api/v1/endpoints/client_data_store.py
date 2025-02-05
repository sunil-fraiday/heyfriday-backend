from typing import Optional, List, Union
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from app.services.client.data_store import ClientDataStoreService
from app.models.mongodb.utils import CredentialManager
from app.models.mongodb.client_data_store import ClientDataStore
from app.models.mongodb.enums import DatabaseType
from app.models.schemas.database_config import PostgresConfig, ClickHouseConfig, WeaviateConfig
from app.schemas.client.structured_data_store import ClientStructuredDataStoreResponse
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/clients/{client_id}/data-stores", tags=["database"])


class DatabaseConfigResponse(BaseModel):
    database_type: str
    config: Union[PostgresConfig, ClickHouseConfig, WeaviateConfig]


DATABASE_TYPE_TO_CONFIG_MAP = {
    DatabaseType.CLICKHOUSE: ClickHouseConfig,
    DatabaseType.POSTGRES: PostgresConfig,
    DatabaseType.WEAVIATE: WeaviateConfig,
}


async def verify_api_key(authorization: Optional[str] = Header(None)):
    """Verify API key from headers"""
    if not authorization:
        raise HTTPException(status_code=403, detail="Missing API key")

    x_api_key = authorization.split(" ")[1]
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


@router.get("/{data_store_id}/credentials", response_model=DatabaseConfigResponse)
async def get_database_config(client_id: str, data_store_id: str, api_key: Optional[str] = Depends(verify_api_key)):
    """
    Get database configuration for a client
    """
    try:
        credential_manager = CredentialManager(current_key=settings.ENCRYPTION_KEY)
        store_service = ClientDataStoreService(credential_manager=credential_manager)
        data_store: ClientDataStore = store_service.get_data_store(client_id=client_id, data_store_id=data_store_id)
        data_store_config = credential_manager.decrypt_config(data_store.config)

        return DatabaseConfigResponse(
            database_type=data_store.database_type,
            config=DATABASE_TYPE_TO_CONFIG_MAP.get(data_store.database_type)(**data_store_config),
        )

    except Exception as e:
        logger.error(f"Error fetching database config for client {client_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ClientStructuredDataStoreResponse])
async def get_database_config(client_id: str):
    """"""
    try:
        credential_manager = CredentialManager(current_key=settings.ENCRYPTION_KEY)
        store_service = ClientDataStoreService(credential_manager=credential_manager)
        data_stores: List[ClientDataStore] = store_service.list_data_stores(client_id=client_id)
        return [
            ClientStructuredDataStoreResponse(
                id=str(data_store.id), database_type=data_store.database_type, is_active=data_store.is_active
            )
            for data_store in data_stores
        ]
    except Exception as e:
        logger.error(f"Error fetching database config for client {client_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
