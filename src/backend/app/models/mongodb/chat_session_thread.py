from mongoengine import fields
from datetime import timedelta

from .base import BaseDocument
from .utils import datetime_utc_now
from .chat_session import ChatSession


class ChatSessionThread(BaseDocument):
    """
    Model to track thread relationships without modifying the core ChatSession model.
    This allows creating logical session boundaries based on inactivity or external triggers
    while maintaining backward compatibility with existing systems.
    """
    
    parent_session_id = fields.StringField(required=True)
    thread_id = fields.StringField(required=True)
    
    # The full composite session_id (parent_id#thread_id)
    thread_session_id = fields.StringField(required=True, unique=True)
    
    chat_session = fields.ReferenceField(ChatSession, required=True)
    active = fields.BooleanField(default=True)
    last_activity = fields.DateTimeField(default=datetime_utc_now)
    metadata = fields.DictField(default={})
    
    meta = {
        "collection": "chat_session_threads",
        "indexes": [
            "parent_session_id", 
            "thread_id",
            "thread_session_id",
            "chat_session",
            "last_activity"
        ]
    }
    
    def is_active(self, inactivity_minutes=1440):
        """Check if this thread is active based on activity time and active flag"""
        if not self.active:
            return False
            
        inactivity_threshold = datetime_utc_now() - timedelta(minutes=inactivity_minutes)
        
        # Ensure both datetimes are timezone-aware for comparison
        last_activity = self.last_activity
        if last_activity.tzinfo is None:
            # If last_activity is naive, assume it's in UTC
            from datetime import timezone
            last_activity = last_activity.replace(tzinfo=timezone.utc)
            
        return last_activity >= inactivity_threshold
    
    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = datetime_utc_now()
        self.save()
        
    def to_serializable_dict(self):
        """Custom serialization with additional fields"""
        data = super().to_serializable_dict()
        data["chat_session_id"] = str(self.chat_session.id)
        return data
