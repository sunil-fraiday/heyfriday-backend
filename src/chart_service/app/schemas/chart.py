from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional
from datetime import datetime


class EntityIdentifierSchema(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    id: str = Field(..., min_length=1, max_length=100)


class IdentifiersSchema(BaseModel):
    service_name: str = Field(..., min_length=1, max_length=50)
    entities: List[EntityIdentifierSchema] = Field(..., min_items=1)


class ChartOptionsSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    figsize: Optional[List[int]] = None
    color: Optional[str] = None
    grid: Optional[bool] = None


class ChartRequestSchema(BaseModel):
    identifiers: IdentifiersSchema
    chart_type: str = Field(..., min_length=1, max_length=20)
    data: Dict[str, Any]
    options: Optional[ChartOptionsSchema] = None
    expiry_hours: Optional[int] = None

    @field_validator("chart_type")
    def validate_chart_type(cls, v):
        valid_types = ["line", "bar", "pie"]
        if v not in valid_types:
            raise ValueError(f"Chart type must be one of {', '.join(valid_types)}")
        return v


class ChartResponseSchema(BaseModel):
    chart_id: str
    url: str


class ChartDetailSchema(BaseModel):
    id: str
    chart_type: str
    created_at: str
    status: str
    url: str
    title: Optional[str] = None
    description: Optional[str] = None


class ChartListResponseSchema(BaseModel):
    charts: List[ChartDetailSchema]
    page: int
    per_page: int
    total: int
