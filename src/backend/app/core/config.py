from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Slack Bot Backend"
    VERSION: str = "0.0.1"

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"

    MONGODB_URI: str

    DATABASE_URL: Optional[str] = None
    TEXT_TO_SQL_SERVICE_URL: Optional[str] = None
    AI_SERVICE_URL: str = TEXT_TO_SQL_SERVICE_URL
    SWYT_WEBHOOK_URL: Optional[str] = None
    API_KEY: str
    ENCRYPTION_KEY: str

    AWS_BEDROCK_ACCESS_KEY_ID: str
    AWS_BEDROCK_SECRET_ACCESS_KEY: str
    AWS_BEDROCK_REGION: str
    AWS_BEDROCK_RUNTIME: Optional[str] = "bedrock-runtime"

    # Celery configurations
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: Optional[str] = None

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def CELERY_BROKER_URL(self) -> str:
        if self.REDIS_PASSWORD: 
            return f"rediss://default:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()
