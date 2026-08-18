from unittest.mock import AsyncMock, MagicMock

from app.db import init_db as init_db_module


async def test_init_db_creates_pgvector_extension(monkeypatch):
    mock_conn = AsyncMock()
    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)

    mock_engine = MagicMock()
    mock_engine.begin = MagicMock(return_value=mock_ctx)
    monkeypatch.setattr(init_db_module, "engine", mock_engine)

    await init_db_module.init_db()

    mock_conn.execute.assert_awaited_once()
    executed_sql = str(mock_conn.execute.await_args.args[0])
    assert "CREATE EXTENSION IF NOT EXISTS vector" in executed_sql
