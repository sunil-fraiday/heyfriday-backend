from enum import Enum


class DatabaseType(str, Enum):
    CLICKHOUSE = "clickhouse"
    POSTGRES = "postgres"
