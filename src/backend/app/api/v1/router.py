from fastapi import APIRouter

from .ga_sql import router as ga_sql_router
from .endpoints.chat_message import router as chat_message_router
from .endpoints.chat_session import router as chat_session_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(chat_message_router)
api_v1_router.include_router(chat_session_router)
api_v1_router.include_router(ga_sql_router)
