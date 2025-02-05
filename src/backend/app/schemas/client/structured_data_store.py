from pydantic import BaseModel, ConfigDict


class ClientDataStoreResponse(BaseModel):
    """Schema for creating a structured data store"""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    database_type: str
    is_active: bool
