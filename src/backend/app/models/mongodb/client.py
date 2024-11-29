from mongoengine import fields
from .base import BaseDocument


class Client(BaseDocument):
    name = fields.StringField(required=True)
    email = fields.EmailField(required=False, default=None)
    keycloak_config = fields.EmbeddedDocumentField(required=False, default=None)

    active = fields.BooleanField(default=True)

    meta = {"collection": "clients", "indexes": ["created_at", "updated_at"]}
