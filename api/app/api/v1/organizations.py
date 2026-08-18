from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_owner
from app.core.security import create_invite_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import InviteCreate, InviteRead

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


@router.post("/invites", response_model=InviteRead, status_code=status.HTTP_201_CREATED)
async def create_invite(
    payload: InviteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
) -> InviteRead:
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    token, expires_at = create_invite_token(
        email=payload.email,
        organization_id=str(current_user.organization_id),
    )
    return InviteRead(invite_token=token, expires_at=expires_at)
