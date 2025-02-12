from abc import ABC, abstractmethod
from typing import List, Dict


class MeasureFilterStrategy(ABC):
    @abstractmethod
    def filter_columns(self, columns: List[Dict]) -> List[Dict]:
        pass


class DefaultMeasureFilter(MeasureFilterStrategy):
    def filter_columns(self, columns: List[Dict]) -> List[Dict]:
        return [
            col
            for col in columns
            if not col["name"].startswith("_") and not col.get("primary_key", False) and self._is_valid_numeric(col)
        ]

    def _is_valid_numeric(self, column: Dict) -> bool:
        numeric_types = {
            "integer",
            "bigint",
            "decimal",
            "numeric",
            "real",
            "double precision",
            "float",
            "int",
            "float",
        }
        return any(t in column["type"].lower() for t in numeric_types)
