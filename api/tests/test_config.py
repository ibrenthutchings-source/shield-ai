import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_loads_required_fields_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
    monkeypatch.setenv("REDIS_URL", "redis://h:6379/0")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+asyncpg://u:p@h:5432/db"
    assert settings.redis_url == "redis://h:6379/0"
    assert settings.jwt_secret_key == "secret"


def test_defaults_are_applied(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
    monkeypatch.setenv("REDIS_URL", "redis://h:6379/0")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")

    settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 60
    assert settings.db_pool_size == 10


def test_missing_required_field_raises(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("REDIS_URL", "redis://h:6379/0")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_allowed_origins_list_parses_and_strips_whitespace(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
    monkeypatch.setenv("REDIS_URL", "redis://h:6379/0")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")
    monkeypatch.setenv("ALLOWED_ORIGINS", " http://a.com ,http://b.com, ")

    settings = Settings(_env_file=None)

    assert settings.allowed_origins_list == ["http://a.com", "http://b.com"]


def test_resolved_celery_urls_fall_back_to_redis_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
    monkeypatch.setenv("REDIS_URL", "redis://h:6379/0")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")
    monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
    monkeypatch.delenv("CELERY_RESULT_BACKEND", raising=False)

    settings = Settings(_env_file=None)

    assert settings.resolved_celery_broker_url == "redis://h:6379/0"
    assert settings.resolved_celery_result_backend == "redis://h:6379/0"


def test_resolved_celery_urls_prefer_explicit_overrides(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
    monkeypatch.setenv("REDIS_URL", "redis://h:6379/0")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://other:6379/1")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://other:6379/2")

    settings = Settings(_env_file=None)

    assert settings.resolved_celery_broker_url == "redis://other:6379/1"
    assert settings.resolved_celery_result_backend == "redis://other:6379/2"


def test_get_settings_is_cached(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
    monkeypatch.setenv("REDIS_URL", "redis://h:6379/0")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")

    from app.core.config import get_settings

    assert get_settings() is get_settings()
