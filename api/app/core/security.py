from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

# bcrypt's underlying algorithm only uses the first 72 bytes of the input.
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    truncated = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(truncated, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    truncated = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(truncated, hashed_password.encode("utf-8"))


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

    subject = payload.get("sub")
    if not subject:
        raise ValueError("Token missing subject")
    return subject


INVITE_EXPIRE_DAYS = 7


def create_invite_token(email: str, organization_id: str) -> tuple[str, int]:
    """Returns (token, expires_at unix timestamp)."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=INVITE_EXPIRE_DAYS)
    payload = {"sub": email, "org_id": organization_id, "type": "invite", "exp": expire}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expire.timestamp())


def decode_invite_token(token: str) -> tuple[str, str]:
    """Returns (email, organization_id)."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired invite token") from exc

    if payload.get("type") != "invite":
        raise ValueError("Token is not an invite token")

    email = payload.get("sub")
    organization_id = payload.get("org_id")
    if not email or not organization_id:
        raise ValueError("Invite token missing claims")
    return email, organization_id
