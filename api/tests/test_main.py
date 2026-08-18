from unittest.mock import AsyncMock

from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok(monkeypatch):
    monkeypatch.setattr("app.main.init_db", AsyncMock())

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "environment" in body


def test_lifespan_calls_init_db_on_startup(monkeypatch):
    mock_init_db = AsyncMock()
    monkeypatch.setattr("app.main.init_db", mock_init_db)

    from app.main import app

    with TestClient(app):
        pass

    mock_init_db.assert_awaited_once()
