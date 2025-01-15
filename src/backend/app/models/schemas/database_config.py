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
    grpc_port: int
    api_key: str
    readonly_api_key: Optional[str] = None
    class_name: Optional[str] = None
    additional_headers: Dict = Field(default_factory=dict)
    timeout_config: Dict = Field(default_factory=dict)


class QdrantConfig(BaseModel):
    """Configuration model for Qdrant instances"""

    url: str
    collection_name: Optional[str] = None
    api_key: str
    https: bool = Field(default=True)
    timeout: float = Field(default=10.0)
