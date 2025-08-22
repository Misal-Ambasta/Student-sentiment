import os
from celery import Celery
from loguru import logger

# Set up logging
logger.add("logs/celery_worker.log", rotation="10 MB", level="INFO")

# Create Celery app
celery_app = Celery(
    "data_processing",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

# Import tasks
celery_app.autodiscover_tasks(['celery_tasks'])

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_max_tasks_per_child=200,
    broker_connection_retry_on_startup=True,
)

if __name__ == '__main__':
    celery_app.start()