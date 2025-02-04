from fastapi import APIRouter

from .endpoints.chat_message import router as chat_message_router
from .endpoints.chat_session import router as chat_session_router
from .endpoints.client import router as client_router
from .endpoints.client_channel import router as client_channel_router
from .endpoints.chat_session_recap import router as chat_session_recap_router
from .endpoints.chat_message_feedback import router as chat_message_feedback_router
from .endpoints.client_data_store import router as client_data_store_router
from .endpoints.semantic_layer.repository import router as repository_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(chat_message_router)
api_v1_router.include_router(chat_session_router)
api_v1_router.include_router(client_router)
api_v1_router.include_router(client_channel_router)
api_v1_router.include_router(chat_session_recap_router)
api_v1_router.include_router(chat_message_feedback_router)
api_v1_router.include_router(client_data_store_router)
api_v1_router.include_router(repository_router)
