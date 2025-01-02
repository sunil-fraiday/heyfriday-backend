from pydantic import BaseModel


class ClientStructuredDataStoreResponse(BaseModel):
    """Schema for creating a structured data store"""

    id: str
    database_type: str
    is_active: bool
