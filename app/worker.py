from app.celery_app import celery

# Example Celery task(s) to validate worker startup
@celery.task(name="app.worker.tasks.example_task")
def example_task(data):
    """Simple example task. Replace with real ingestion/analysis tasks in Phase 2."""
    print("[worker] Processing:", data)
    return {"status": "processed", "input": data}
