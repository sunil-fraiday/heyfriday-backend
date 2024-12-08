from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Union

from app.models.mongodb.client_channel import ChannelType


class WebhookChannelConfig(BaseModel):
    webhook_url: str
    headers: Optional[Dict] = None


class SlackWebhookConfig(BaseModel):
    webhook_url: str
    headers: Optional[Dict] = None


class ClientChannelCreateorUpdateRequest(BaseModel):
    channel_type: ChannelType
    channel_config: Union[WebhookChannelConfig, SlackWebhookConfig]
    is_active: Optional[bool] = True


class ClientChannelResponse(BaseModel):
    id: str
    channel_type: ChannelType
    channel_config: Union[WebhookChannelConfig, SlackWebhookConfig]
    is_active: bool
