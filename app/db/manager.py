import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async engine (SQLAlchemy 2.0 style). DATABASE_URL should use asyncpg driver.
engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db() -> None:
    """
    Ensure the pgvector extension exists and run any minimal DB initialization.
    Call on application startup before migrations.

    Note: creating extensions typically requires superuser privileges. It's
    recommended that extensions be provisioned by an administrator or by the
    database provisioning/migration pipeline. If the application cannot create
    the extension, a clear error will be raised with remediation steps.
    """
    async with engine.begin() as conn:
        try:
            # Ensure pgvector extension exists. Requires a superuser role on first create;
            # `IF NOT EXISTS` makes it safe to call multiple times.
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        except Exception as exc:
            logger.exception("Failed to ensure pgvector extension exists. Ensure the extension is installed by a superuser or include it in DB provisioning/migrations.")
            raise RuntimeError(
                "Failed to ensure pgvector extension exists. Install the extension as a superuser or ensure your DATABASE_URL points to a user with sufficient privileges."
            ) from exc
        # Additional DB initialization steps (migrations) should run after this
