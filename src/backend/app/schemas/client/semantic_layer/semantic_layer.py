from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from app.schemas.client.semantic_layer.repository import RepositoryInline
from app.schemas.client.semantic_layer.semantic_server import SemanticServerInline
from app.schemas.client.client import ClientInline
from app.schemas.client.structured_data_store import ClientDataStoreResponse
from app.models.mongodb.semantic_layer.client_semantic_layer import ClientSemanticLayer


class SemanticLayerCreate(BaseModel):
    semantic_server_id: str
    repository_id: str


class SemanticLayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    client: ClientInline
    client_repository: RepositoryInline
    client_semantic_server: SemanticServerInline
    repository_folder: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db_model(cls, db_model: ClientSemanticLayer) -> "SemanticLayerResponse":
        return cls(
            id=str(db_model.id),
            client=ClientInline.model_validate(db_model.client.to_serializable_dict()),
            client_repository=RepositoryInline.model_validate(db_model.client_repository.to_serializable_dict()),
            client_semantic_server=SemanticServerInline.model_validate(
                db_model.client_semantic_server.to_serializable_dict()
            ),
            repository_folder=db_model.repository_folder,
            is_active=db_model.is_active,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
        )


class AddorRemoveDataStoreRequest(BaseModel):
    data_store_id: str
