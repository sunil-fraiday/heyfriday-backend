from datetime import datetime
from datetime import timezone


def datetime_utc_now():
    return datetime.now(timezone.utc)
