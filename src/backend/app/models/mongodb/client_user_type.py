from mongoengine import fields

from .base import BaseDocument
from .client import Client


class ClientUserType(BaseDocument):
    """
    Model to store custom user types for clients.
    These custom types can be used as sender_type in chat messages.
    """
    client = fields.ReferenceField(Client, required=True)
    type_id = fields.StringField(required=True)  # Unique identifier for this user type within the client
    name = fields.StringField(required=True)     # Display name for the user type
    description = fields.StringField(required=False)
    
    # Additional metadata for the user type
    metadata = fields.DictField(default={})
    
    # Controls whether this user type is active
    is_active = fields.BooleanField(default=True)
    
    meta = {
        "collection": "client_user_types",
        "indexes": [
            "created_at", 
            "client",
            {"fields": ["client", "type_id"], "unique": True}
        ]
    }
    
    @classmethod
    def get_active_types_for_client(cls, client_id):
        """Get all active user types for a specific client"""
        return cls.objects(client=client_id, is_active=True)
