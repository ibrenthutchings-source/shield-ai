from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.models.user import User
from scripts.seed import SeedConfigError, seed_user


@pytest.fixture
def patched_session(db_session):
    """Point the seed script's session factory at the test's in-memory DB."""

    def _factory():
        return db_session

    with patch("scripts.seed.AsyncSessionLocal", _factory):
        yield db_session


async def test_seed_creates_user(patched_session, monkeypatch):
    monkeypatch.setenv("SEED_USER_EMAIL", "seed@shieldai.dev")
    monkeypatch.setenv("SEED_USER_PASSWORD", "supersecret1")
    monkeypatch.setenv("SEED_USER_ORG_NAME", "Seeded Org")

    await seed_user()

    result = await patched_session.execute(select(User).where(User.email == "seed@shieldai.dev"))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.org_name == "Seeded Org"
    assert user.hashed_password != "supersecret1"


async def test_seed_uses_default_org_name(patched_session, monkeypatch):
    monkeypatch.setenv("SEED_USER_EMAIL", "seed2@shieldai.dev")
    monkeypatch.setenv("SEED_USER_PASSWORD", "supersecret1")
    monkeypatch.delenv("SEED_USER_ORG_NAME", raising=False)

    await seed_user()

    result = await patched_session.execute(select(User).where(User.email == "seed2@shieldai.dev"))
    assert result.scalar_one_or_none().org_name == "ShieldAI"


async def test_seed_is_idempotent(patched_session, monkeypatch):
    monkeypatch.setenv("SEED_USER_EMAIL", "seed3@shieldai.dev")
    monkeypatch.setenv("SEED_USER_PASSWORD", "supersecret1")

    await seed_user()
    await seed_user()

    result = await patched_session.execute(select(User).where(User.email == "seed3@shieldai.dev"))
    assert len(result.scalars().all()) == 1


async def test_seed_requires_email(monkeypatch):
    monkeypatch.delenv("SEED_USER_EMAIL", raising=False)
    monkeypatch.setenv("SEED_USER_PASSWORD", "supersecret1")

    with pytest.raises(SeedConfigError, match="SEED_USER_EMAIL"):
        await seed_user()


async def test_seed_requires_password(monkeypatch):
    monkeypatch.setenv("SEED_USER_EMAIL", "seed4@shieldai.dev")
    monkeypatch.delenv("SEED_USER_PASSWORD", raising=False)

    with pytest.raises(SeedConfigError, match="SEED_USER_PASSWORD"):
        await seed_user()
