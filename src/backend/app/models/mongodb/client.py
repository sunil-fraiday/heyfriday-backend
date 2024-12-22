from pydantic import BaseModel

from mongoengine import fields
from .base import BaseDocument
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KeycloakConfig(BaseModel):
    realm: str
    client_id: str
    client_secret: str
    server_url: str

    admin_username: str
    admin_password: str


class Client(BaseDocument):
    name = fields.StringField(required=True)
    email = fields.EmailField(required=False, default=None)
    client_id = fields.StringField(required=True, unique=True)
    client_key = fields.StringField(required=True, unique=True)
    keycloak_config = fields.DictField(required=False, default=None)

    is_active = fields.BooleanField(default=True)

    meta = {"collection": "clients", "indexes": ["created_at", "updated_at", "client_id"]}

    def get_keycloak_config(self):
        try:
            return KeycloakConfig(**self.keycloak_config)
        except Exception as e:
            logger.error(f"Error parsing keycloak config: {e}")
            return None
