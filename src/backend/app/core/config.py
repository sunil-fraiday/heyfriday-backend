from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


PROJECT_ROOT = Path(__file__).parent.parent.resolve()

print(PROJECT_ROOT)

print(f"Looking for .env at: {PROJECT_ROOT / '.env'}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / '.env', env_file_encoding='utf-8', extra = "ignore")
    
    PROJECT_NAME: str = "Slack Bot Backend"
    VERSION: str = "0.0.1"

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"

    DATABASE_URL: Optional[str] = None

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"



settings = Settings()

