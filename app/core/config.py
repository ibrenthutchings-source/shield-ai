import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Instantiate and perform lightweight validation to fail fast on misconfiguration
settings = Settings()

# Basic runtime checks with actionable errors
if not settings.SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Set the SECRET_KEY environment variable or provide it via your secret manager.")

# Ensure DATABASE_URL references an async-capable driver (common pattern: 'postgresql+asyncpg://')
_db_url = (settings.DATABASE_URL or "").lower()
if "asyncpg" not in _db_url and "postgresql+" not in _db_url:
    logger.warning("DATABASE_URL does not appear to reference an async driver (e.g., 'postgresql+asyncpg://'). If using SQLAlchemy async engine, ensure the URL uses an async driver.")

# Very small sanity check for REDIS_URL
_redis_url = (settings.REDIS_URL or "").lower()
if not (_redis_url.startswith("redis://") or _redis_url.startswith("rediss://") or _redis_url.startswith("redis+")):
    logger.warning("REDIS_URL does not use a redis scheme (redis:// or rediss://). Double-check your REDIS_URL value.")
