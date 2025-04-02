from celery import Celery
from functools import lru_cache

from .config import settings


@lru_cache()
def get_celery_settings():
    default_queue = settings.CELERY_DEFAULT_QUEUE
    events_queue = settings.CELERY_EVENTS_QUEUE
    
    return {
        "broker_url": settings.CELERY_BROKER_URL or settings.get_redis_url(),
        # "result_backend": settings.CELERY_RESULT_BACKEND,
        "task_annotations": {"*": {"rate_limit": "25/s"}},
        "worker_send_task_events": True,
        "task_send_sent_event": True,
        "task_queues": {
            default_queue: {
                "exchange": default_queue,
                "exchange_type": "direct",
                "routing_key": default_queue,
            },
            events_queue: {
                "exchange": events_queue,
                "exchange_type": "direct",
                "routing_key": events_queue,
            },
        },
        "task_routes": {
            "app.tasks.*": {"queue": default_queue},
            "app.tasks.events.*": {"queue": events_queue},
        },
    }


def create_celery_app() -> Celery:
    celery_app = Celery("backend_tasks")

    # Load configuration
    celery_settings = get_celery_settings()
    celery_app.conf.update(celery_settings)

    # Auto-discover tasks
    celery_app.autodiscover_tasks(["app.tasks"])

    return celery_app


celery_app = create_celery_app()
