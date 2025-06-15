from mongoengine import fields

from app.models.mongodb.base import BaseDocument


class WorkflowConfig(BaseDocument):
    """
    Configuration for workflow routing based on client and client channel.
    Defines which workflow ID to use for specific clients and channels.
    """
    name = fields.StringField(required=True)
    description = fields.StringField()
    client = fields.ReferenceField("Client", required=True)
    client_channel = fields.ReferenceField("ClientChannel", required=False)
    workflow_id = fields.StringField(required=True)
    is_active = fields.BooleanField(default=True)

    meta = {
        "collection": "workflow_configs",
        "indexes": [
            "client",
            "client_channel",
            "is_active",
            ("client", "client_channel", "is_active"),
        ],
    }
