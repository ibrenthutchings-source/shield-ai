from celery import Celery
from app.core.config import settings

# Celery configuration using Redis as broker and backend
celery = Celery(
    "shieldai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Basic routing; extend in Phase 2
celery.conf.task_routes = {"app.worker.tasks.*": {"queue": "default"}}
