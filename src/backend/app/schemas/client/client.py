from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict


class ClientCreateorUpdateRequest(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True


class ClientResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    email: Optional[EmailStr] = None
    client_id: str
    is_active: bool

    class Config:
        allow_population_by_field_name = True
