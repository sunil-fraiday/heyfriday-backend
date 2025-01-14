from mongoengine import fields
from .base import BaseDocument


class ClientDataStoreTenant(BaseDocument):
    client_data_store = fields.ReferenceField("ClientDataStore", required=True)

    tenant_id = fields.StringField(required=True, unique=True)
    name = fields.StringField(required=True)
    metadata = fields.DictField(default=dict)
    is_active = fields.BooleanField(default=True)

    meta = {
        "collection": "client_data_store_tenants",
        "indexes": [
            "client_data_store",
            "tenant_id",
            ("client_data_store", "tenant_id", "is_active"),
        ],
    }

    def __str__(self):
        return f"Tenant {self.tenant_id} ({self.name})"
