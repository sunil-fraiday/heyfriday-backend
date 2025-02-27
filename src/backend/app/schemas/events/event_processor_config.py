from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field

from app.models.mongodb.events.event_types import EventType, EntityType
from app.models.mongodb.events.event_processor_config import ProcessorType
from app.models.schemas.processor_config import HttpWebhookConfig, AmqpConfig


class ProcessorConfigCreate(BaseModel):
    """Schema for creating a new processor configuration"""

    name: str
    client_id: str
    processor_type: ProcessorType
    config: Union[HttpWebhookConfig, AmqpConfig, Dict[str, Any]]
    event_types: List[EventType]
    entity_types: List[EntityType]
    description: Optional[str] = Field(None)
    is_active: bool = Field(default=True)


class ProcessorConfigUpdate(BaseModel):
    """Schema for updating an existing processor configuration"""

    name: Optional[str] = Field(None)
    config: Optional[Union[HttpWebhookConfig, AmqpConfig, Dict[str, Any]]] = Field(None)
    event_types: Optional[List[EventType]] = Field(None)
    entity_types: Optional[List[EntityType]] = Field(None)
    description: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)


class ProcessorConfigResponse(BaseModel):
    """Schema for processor configuration response"""

    id: str
    name: str
    client_id: str
    processor_type: str
    config: Dict[str, Any]  # We use Dict here to handle any processor type
    event_types: List[str]
    entity_types: List[str]
    description: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str
