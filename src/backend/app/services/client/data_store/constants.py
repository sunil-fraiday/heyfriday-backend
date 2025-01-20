from .postgres import PostgresService
from .weaviate import WeaviateService
from .clickhouse import ClickHouseService

from app.models.mongodb.enums import DatabaseType


DATABASE_TYPE_TO_SERVICE_MAP = {
    DatabaseType.CLICKHOUSE: ClickHouseService,
    DatabaseType.POSTGRES: PostgresService,
    DatabaseType.WEAVIATE: WeaviateService,
}
