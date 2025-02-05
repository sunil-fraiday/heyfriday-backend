from typing import Optional, Dict
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from app.models.mongodb.semantic_layer.config_models import SemanticEngineType


class SemanticConfigCreate(BaseModel):
    api_url: str
    api_token: str
    dev_mode: bool = False
    additional_config: Dict = Field(default_factory=dict)


class SemanticServerCreate(BaseModel):
    server_name: str
    engine_type: SemanticEngineType
    semantic_config: SemanticConfigCreate
    client_id: Optional[str] = None
    is_default: bool = False


class SemanticServerResponse(BaseModel):
    id: str
    server_name: str
    semantic_config: SemanticConfigCreate
    client_id: Optional[str] = None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime


class SemanticServerInline(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    server_name: str
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    client_id: Optional[str] = None
