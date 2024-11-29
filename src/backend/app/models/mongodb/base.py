from mongoengine import Document, fields
from .utils import datetime_utc_now


class BaseDocument(Document):
    created_at = fields.DateTimeField(default=datetime_utc_now)
    updated_at = fields.DateTimeField(default=datetime_utc_now)

    meta = {"abstract": True}
