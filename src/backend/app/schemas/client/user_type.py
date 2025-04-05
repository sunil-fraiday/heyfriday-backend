from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class ClientUserTypeCreate(BaseModel):
    """Schema for creating a new client user type"""
    type_id: str = Field(..., description="Unique identifier for this user type within the client")
    name: str = Field(..., description="Display name for the user type")
    description: Optional[str] = Field(None, description="Optional description of the user type")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata for the user type")


class ClientUserTypeUpdate(BaseModel):
    """Schema for updating an existing client user type"""
    name: Optional[str] = Field(None, description="Display name for the user type")
    description: Optional[str] = Field(None, description="Optional description of the user type")
    metadata: Optional[Dict] = Field(None, description="Additional metadata for the user type")
    is_active: Optional[bool] = Field(None, description="Whether this user type is active")


class ClientUserTypeResponse(BaseModel):
    """Schema for client user type response"""
    id: str = Field(..., description="MongoDB ID of the user type")
    client_id: str = Field(..., description="ID of the client this user type belongs to")
    type_id: str = Field(..., description="Unique identifier for this user type within the client")
    name: str = Field(..., description="Display name for the user type")
    description: Optional[str] = Field(None, description="Optional description of the user type")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata for the user type")
    is_active: bool = Field(..., description="Whether this user type is active")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    
    @staticmethod
    def from_db_model(model):
        """Convert a database model to a response schema"""
        return ClientUserTypeResponse(
            id=str(model.id),
            client_id=str(model.client.id),
            type_id=model.type_id,
            name=model.name,
            description=model.description,
            metadata=model.metadata,
            is_active=model.is_active,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat()
        )


class ClientUserTypesResponse(BaseModel):
    """Schema for a list of client user types"""
    items: List[ClientUserTypeResponse]
    total: int
