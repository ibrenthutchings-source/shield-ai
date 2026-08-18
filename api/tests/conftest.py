import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

from app.core.config import get_settings  # noqa: E402
from app.db.session import Base  # noqa: E402
from app.main import app  # noqa: E402
import app.models  # noqa: E402,F401 register ORM models on Base.metadata


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def db_session():
    """A fresh in-memory SQLite DB per test, shared across a session via StaticPool."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def client(db_session, monkeypatch):
    from unittest.mock import AsyncMock

    from fastapi.testclient import TestClient

    from app.db.session import get_db

    monkeypatch.setattr("app.main.init_db", AsyncMock())

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "agent-user@school.org", "password": "supersecret1", "org_name": "Org"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "agent-user@school.org", "password": "supersecret1"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
