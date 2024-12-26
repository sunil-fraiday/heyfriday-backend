from mongoengine import fields, CASCADE

from .base import BaseDocument
from .chat_message import ChatMessage


class ChatMessageFeedback(BaseDocument):
    chat_message = fields.ReferenceField(ChatMessage, required=True, reverse_delete_rule=CASCADE)
    rating = fields.IntField(required=True)
    comment = fields.StringField(required=False)
    metadata = fields.DictField(required=False, default=dict)

    meta = {
        "collection": "chat_message_feedbacks",
        "indexes": [
            "created_at",
            "chat_message",
            ("chat_message", "-created_at"),
        ],
    }

    def __str__(self):
        return f"Feedback for message {self.chat_message.id} - Rating: {self.rating}"
