from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict


class BaseProcessorConfig(BaseModel):
    """Base configuration with common fields for all processor types"""

    model_config = ConfigDict(extra="forbid")


class HttpWebhookConfig(BaseProcessorConfig):
    """HTTP Webhook processor configuration"""

    webhook_url: HttpUrl = Field(..., description="Webhook endpoint URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers to include")
    timeout: int = Field(default=10, ge=1, le=60, description="Request timeout in seconds")

    @field_validator("headers")
    def validate_headers(cls, v):
        """Validate headers contain only string values"""
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("Headers must contain only string keys and values")
        return v


class AmqpConfig(BaseProcessorConfig):
    """AMQP processor configuration"""

    host: str = Field(..., description="AMQP broker hostname")
    port: int = Field(default=5672, ge=1, le=65535, description="AMQP broker port")
    vhost: str = Field(default="/", description="Virtual host")
    exchange: str = Field(default="", description="Exchange name")
    routing_key: str = Field(..., description="Routing key for messages")
    username: Optional[str] = Field(None, description="AMQP username")
    password: Optional[str] = Field(None, description="AMQP password")

    @field_validator("routing_key")
    def validate_routing_key(cls, v):
        if not v or not v.strip():
            raise ValueError("Routing key cannot be empty")
        return v

    @field_validator("host")
    def validate_host(cls, v):
        if not v or not v.strip():
            raise ValueError("Host cannot be empty")
        return v
