import logging
from fastapi import FastAPI
from app.db.manager import init_db

logger = logging.getLogger(__name__)
app = FastAPI(title="shield-ai-api")

@app.on_event("startup")
async def _startup():
    try:
        await init_db()
    except Exception as exc:
        # Use structured logging and fail startup so the process doesn't run in a degraded state
        logger.exception("DB init failed during startup")
        raise

@app.get("/health")
async def health():
    return {"status": "ok"}
