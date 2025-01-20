from app.models.mongodb.enums import DatabaseType, EngineType
from app.models.schemas.database_config import ClickHouseConfig, PostgresConfig, WeaviateConfig

BOT_SENDER_NAME = "fraiday-bot"


DATABASE_TYPE_TO_ENGINE_MAP = {
    DatabaseType.CLICKHOUSE: EngineType.STRUCTURED,
    DatabaseType.POSTGRES: EngineType.UNSTRUCTURED,
    DatabaseType.WEAVIATE: EngineType.UNSTRUCTURED,
    DatabaseType.QDRANT: EngineType.UNSTRUCTURED,
}


DATABASE_TYPE_TO_CONFIG_MAP = {
    DatabaseType.CLICKHOUSE: ClickHouseConfig,
    DatabaseType.POSTGRES: PostgresConfig,
    DatabaseType.WEAVIATE: WeaviateConfig,
}
