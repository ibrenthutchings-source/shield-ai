from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.core.config import settings

# Create async engine (SQLAlchemy 2.0 style). DATABASE_URL should use asyncpg driver.
engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db() -> None:
    """
    Ensure the pgvector extension exists and run any minimal DB initialization.
    Call on application startup before migrations.
    """
    async with engine.begin() as conn:
        # Ensure pgvector extension exists. Requires a superuser role on first create;
        # `IF NOT EXISTS` makes it safe to call multiple times.
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        # Additional DB initialization steps (migrations) should run after this
