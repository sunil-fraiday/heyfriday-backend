# Import all models here to ensure they are registered with MongoEngine

# Define exported symbols
__all__ = [
    'BaseDocument',
    'Client',
    'ChatSession',
    'ChatMessage',
    'Attachment',
    'SenderType',
    'ChatSessionThread',
    'ClientChannel',
    'datetime_utc_now',  # from utils
]

# Base models and utils
from .base import BaseDocument
from .utils import datetime_utc_now

# Core models
from .client import Client
from .chat_session import ChatSession
from .chat_message import ChatMessage, Attachment, SenderType
from .chat_session_thread import ChatSessionThread
from .client_channel import ClientChannel

# Make sure any reference models are imported before models that reference them
