from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from datetime import datetime


class RepositoryConfigCreate(BaseModel):
    repo_url: str
    branch: str = Field(default="main")
    api_key: str
    base_path: str = Field(default="")


class RepositoryCreate(BaseModel):
    repository_config: RepositoryConfigCreate
    client_id: Optional[str] = None
    is_default: bool = False


class RepositoryResponse(BaseModel):
    id: str
    repository_config: RepositoryConfigCreate
    client_id: Optional[str] = None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime


class RepositoryInline(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    repository_config: RepositoryConfigCreate
    client_id: Optional[str] = None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime