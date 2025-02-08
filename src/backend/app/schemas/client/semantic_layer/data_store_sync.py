from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class DataStoreSyncStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    latest_job_id: Optional[str] = None
    latest_sync_status: Optional[str] = None
    latest_sync_at: Optional[datetime] = None
    can_requeue: bool = False
    logs: List[str] = []


class DataStoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    engine_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    sync_status: DataStoreSyncStatus
