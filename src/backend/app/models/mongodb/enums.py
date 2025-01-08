from enum import Enum


class DatabaseType(str, Enum):
    CLICKHOUSE = "clickhouse"
    POSTGRES = "postgres"
    QDRANT = "qdrant"


class EngineType(str, Enum):
    STRUCTURED = "structured"
    UNSTRUCTURED = "unstructured"


class ExecutionStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
