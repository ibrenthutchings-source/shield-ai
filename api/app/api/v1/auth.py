import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    decode_invite_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.user import InviteAccept, Token, UserCreate, UserRead

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


async def _reload_with_organization(db: AsyncSession, user_id: uuid.UUID) -> User:
    """Re-select so the joined-load `organization` relationship is populated for the response."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    """Creates a brand-new organization with this user as its owner."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    organization = Organization(name=payload.org_name)
    db.add(organization)
    await db.flush()

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        organization_id=organization.id,
        role="owner",
    )
    db.add(user)
    await db.commit()
    return await _reload_with_organization(db, user.id)


@router.post("/register-invited", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_invited(payload: InviteAccept, db: AsyncSession = Depends(get_db)) -> User:
    """Joins an existing organization as a member, using a token from an owner's invite."""
    try:
        email, organization_id = decode_invite_token(payload.invite_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    organization = await db.get(Organization, uuid.UUID(organization_id))
    if organization is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization no longer exists")

    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        organization_id=organization.id,
        role="member",
    )
    db.add(user)
    await db.commit()
    return await _reload_with_organization(db, user.id)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return Token(access_token=create_access_token(subject=str(user.id)))
