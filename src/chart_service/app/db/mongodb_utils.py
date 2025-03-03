from app.config import settings

from mongoengine import connect, disconnect


def connect_to_db():
    return connect(host=settings.MONGODB_URI, uuidRepresentation="standard")


def disconnect_from_db():
    return disconnect()
