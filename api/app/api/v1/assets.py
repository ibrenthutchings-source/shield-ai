from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.redteam_agent import RedTeamSimulationAgent
from app.api.v1.deps import get_current_user, get_redteam_agent
from app.db.session import get_db
from app.models.asset import Asset
from app.models.user import User
from app.schemas.asset import DiscoveredAsset
from app.schemas.asset_api import AssetRead
from app.ws.connection_manager import connection_manager

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
async def create_asset(
    payload: DiscoveredAsset,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agent: RedTeamSimulationAgent = Depends(get_redteam_agent),
) -> Asset:
    assessment = agent.assess([payload])

    asset = Asset(
        user_id=current_user.id,
        host=payload.host,
        port=payload.port,
        service=payload.service,
        tls_valid=payload.tls_valid,
        oauth_scope_excessive=payload.oauth_scope_excessive,
        risk_findings=[f.model_dump(mode="json") for f in assessment.findings],
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    await connection_manager.broadcast(
        current_user.id,
        {
            "agent": "redteam_simulation",
            "status": "completed",
            "asset_host": payload.host,
            "risk_score": assessment.overall_risk_score,
        },
    )

    return asset


@router.get("", response_model=list[AssetRead])
async def list_assets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Asset]:
    result = await db.execute(
        select(Asset).where(Asset.user_id == current_user.id).order_by(Asset.created_at.desc())
    )
    return list(result.scalars().all())
