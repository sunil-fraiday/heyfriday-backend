from pydantic import BaseModel
from typing import Optional, Dict, List

# Old models remove them after refactoring
class MessageRequest(BaseModel):
    message: str
    user: str
    channel: str
    thread_ts: Optional[str] = None
    thread_context: Optional[str] = None


class MessageResponse(BaseModel):
    message: Optional[str] = None
    sql_data: Optional[List[Dict]] = None
    image_url: Optional[str] = None
