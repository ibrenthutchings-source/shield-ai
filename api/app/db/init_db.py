import logging

from sqlalchemy import text

from app.db.session import engine

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Ensure the pgvector extension exists before any model migrations run."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    logger.info("pgvector extension verified")
