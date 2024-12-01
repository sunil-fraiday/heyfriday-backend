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

    AWS_BEDROCK_ACCESS_KEY_ID: str
    AWS_BEDROCK_SECRET_ACCESS_KEY: str
    AWS_BEDROCK_REGION :str
    AWS_BEDROCK_RUNTIME: Optional[str] = "bedrock-runtime"

    # Celery configurations
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    CELERY_BROKER_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
