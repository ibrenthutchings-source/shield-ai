import logging
from app.celery_app import celery

logger = logging.getLogger(__name__)

# Example Celery task(s) to validate worker startup
@celery.task(name="app.worker.tasks.example_task")
def example_task(data):
    """Simple example task. Replace with real ingestion/analysis tasks in Phase 2."""
    logger.info("[worker] Processing: %s", data)
    return {"status": "processed", "input": data}
