import importlib


def test_celery_app_falls_back_to_redis_url_when_no_explicit_broker(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
    monkeypatch.setenv("REDIS_URL", "redis://h:6379/0")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")
    monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
    monkeypatch.delenv("CELERY_RESULT_BACKEND", raising=False)

    from app.core.config import get_settings

    get_settings.cache_clear()

    import app.worker as worker_module

    importlib.reload(worker_module)

    assert worker_module.celery_app.conf.broker_url == "redis://h:6379/0"
    assert worker_module.celery_app.conf.result_backend == "redis://h:6379/0"
