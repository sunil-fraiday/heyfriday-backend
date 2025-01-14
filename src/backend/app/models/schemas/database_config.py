from pydantic import BaseModel, Field
from typing import Dict, Optional


class DatabaseConfig(BaseModel):
    """Base configuration model for database credentials"""

    database: str
    user: str
    password: str
    host: str = Field(default="localhost")
    port: int


class ClickHouseConfig(DatabaseConfig):
    """ClickHouse specific configuration"""

    port: int = Field(default=9000)
    secure: bool = Field(default=True)


class PostgresConfig(DatabaseConfig):
    """PostgreSQL specific configuration"""

    port: int = Field(default=5432)


class WeaviateConfig(BaseModel):
    """Configuration model for Weaviate instances"""

    url: str
    api_key: str
    class_name: Optional[str] = None
    additional_headers: Dict = Field(default_factory=dict)
    timeout_config: Dict = Field(default_factory=dict)
    tenant_config: Dict[str, str] = Field(default_factory=dict)
