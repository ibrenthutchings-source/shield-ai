from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.db.session import AsyncSessionLocal, Base, engine, get_db


def test_engine_is_async_engine():
    assert isinstance(engine, AsyncEngine)


def test_session_factory_produces_async_session():
    session = AsyncSessionLocal()
    assert isinstance(session, AsyncSession)


def test_base_has_metadata_for_orm_models():
    assert hasattr(Base, "metadata")


async def test_get_db_yields_a_single_async_session():
    gen = get_db()
    session = await gen.__anext__()
    try:
        assert isinstance(session, AsyncSession)
    finally:
        await gen.aclose()
