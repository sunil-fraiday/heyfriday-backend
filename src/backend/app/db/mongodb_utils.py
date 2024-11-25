from app.core.config import settings

from mongoengine import connect, disconnect


def connect_to_db():
    return connect(host=settings.MONGODB_URI)


def disconnect_from_db():
    return disconnect()
