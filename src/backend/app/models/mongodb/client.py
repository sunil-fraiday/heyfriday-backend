from mongoengine import fields
from .base import BaseDocument


class Client(BaseDocument):
    name = fields.StringField(required=True)
    email = fields.EmailField(required=False, default=None)
    client_id = fields.StringField(required=True, unique=True)
    client_key = fields.StringField(required=True, unique=True)
    keycloak_config = fields.DictField(required=False, default=None)

    is_active = fields.BooleanField(default=True)

    meta = {"collection": "clients", "indexes": ["created_at", "updated_at", "client_id"]}
