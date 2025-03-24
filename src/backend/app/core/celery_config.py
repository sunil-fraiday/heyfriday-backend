from celery import Celery
from functools import lru_cache

from .config import settings


@lru_cache()
def get_celery_settings():
    return {
        "broker_url": settings.CELERY_BROKER_URL or settings.get_redis_url(),
        # "result_backend": settings.CELERY_RESULT_BACKEND,
        "task_annotations": {"*": {"rate_limit": "25/s"}},
        "task_queues": {
            "celery": {
                "exchange": "celery",
                "exchange_type": "direct",
                "routing_key": "celery",
            },
            "events": {
                "exchange": "events",
                "exchange_type": "direct",
                "routing_key": "events",
            },
        },
        "task_routes": {
            "app.tasks.*": {"queue": "celery"},
            "app.tasks.events.*": {"queue": "events"},
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
