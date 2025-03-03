from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).parent.resolve()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Chart Generation Service"
    DEBUG: bool = Field(default=False, env="DEBUG")

    MONGODB_URI: str

    AZURE_STORAGE_CONNECTION_STRING: str = Field(default="")
    AZURE_CONTAINER_NAME: str = Field(default="charts")

    DEFAULT_CHART_EXPIRY_HOURS: int = Field(default=168)


settings = Settings()
