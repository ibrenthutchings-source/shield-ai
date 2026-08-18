import logging

from sqlalchemy import text

from app import models  # noqa: F401 register ORM models on Base.metadata
from app.db.session import Base, engine

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Ensure the pgvector extension and ORM tables exist before serving requests.

    There's no Alembic migration chain yet, so this creates tables directly
    from the current models. Once real migrations are introduced, this
    should defer to `alembic upgrade head` instead.
    """
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("pgvector extension and tables verified")
