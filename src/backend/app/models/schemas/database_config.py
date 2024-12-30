from pydantic import BaseModel, Field
from typing import Dict


class DatabaseConfig(BaseModel):
    """Base configuration model for database credentials"""

    database: str
    username: str
    password: str
    host: str = Field(default="localhost")
    port: int
    additional_params: Dict = Field(default={})


class ClickHouseConfig(DatabaseConfig):
    """ClickHouse specific configuration"""

    port: int = Field(default=9000)
    secure: bool = Field(default=True)


class PostgresConfig(DatabaseConfig):
    """PostgreSQL specific configuration"""

    port: int = Field(default=5432)
    ssl_mode: str = Field(default="prefer")
