"""Seed an initial user account.

Reads credentials from the environment so no real password ever lives in
source control. Idempotent: re-running with the same email is a no-op.

Usage:
    SEED_USER_EMAIL=admin@example.org \\
    SEED_USER_PASSWORD=... \\
    SEED_USER_ORG_NAME="Example Org" \\
    python -m scripts.seed
"""

import asyncio
import os
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User


class SeedConfigError(RuntimeError):
    pass


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SeedConfigError(f"{name} must be set to seed a user")
    return value


async def seed_user() -> None:
    """Creates a new organization with this user as its owner, if the email isn't taken yet."""
    email = _require_env("SEED_USER_EMAIL")
    password = _require_env("SEED_USER_PASSWORD")
    org_name = os.environ.get("SEED_USER_ORG_NAME", "ShieldAI")

    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            print(f"User {email} already exists, skipping.")
            return

        organization = Organization(name=org_name)
        session.add(organization)
        await session.flush()

        user = User(
            email=email,
            hashed_password=hash_password(password),
            organization_id=organization.id,
            role="owner",
        )
        session.add(user)
        await session.commit()
        print(f"Created user {email}, owner of organization {org_name!r}.")


def main() -> None:
    try:
        asyncio.run(seed_user())
    except SeedConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
