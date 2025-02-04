from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict


class ClientCreateorUpdateRequest(BaseModel):
    name: str
    client_id: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True


class ClientResponse(BaseModel):
    id: str
    name: str
    email: Optional[EmailStr] = None
    client_id: str
    is_active: bool

    class Config:
        populate_by_name = True
