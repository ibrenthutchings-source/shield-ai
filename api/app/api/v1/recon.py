import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.recon_agent import AttackSurfaceReconAgent
from app.agents.redteam_agent import RedTeamSimulationAgent
from app.api.v1.deps import get_current_user, get_redteam_agent
from app.db.session import get_db
from app.models.asset import Asset
from app.models.user import User
from app.schemas.asset_api import AssetRead
from app.schemas.recon import ReconTarget
from app.ws.connection_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/recon", tags=["recon"])


def get_recon_agent() -> AttackSurfaceReconAgent:
    return AttackSurfaceReconAgent()


@router.post("/scan", response_model=list[AssetRead], status_code=status.HTTP_201_CREATED)
async def scan_domain(
    payload: ReconTarget,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    recon_agent: AttackSurfaceReconAgent = Depends(get_recon_agent),
    redteam_agent: RedTeamSimulationAgent = Depends(get_redteam_agent),
) -> list[Asset]:
    """Passively audits a domain, maps findings to MITRE ATT&CK, and stores the resulting assets."""
    await connection_manager.broadcast(
        current_user.organization_id,
        {"agent": "attack_surface_recon", "status": "started", "domain": payload.domain},
    )

    try:
        result = await recon_agent.scan(payload.domain)
    except Exception:
        logger.exception("Recon scan failed for %s", payload.domain)
        await connection_manager.broadcast(
            current_user.organization_id,
            {"agent": "attack_surface_recon", "status": "error", "domain": payload.domain},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recon scan is temporarily unavailable",
        )

    assessment = redteam_agent.assess(result.assets)
    findings_by_asset: dict[tuple[str, int | None, str | None], list] = {}
    for finding in assessment.findings:
        key = (finding.asset.host, finding.asset.port, finding.asset.service)
        findings_by_asset.setdefault(key, []).append(finding)

    created: list[Asset] = []
    for discovered in result.assets:
        key = (discovered.host, discovered.port, discovered.service)
        risk_findings = findings_by_asset.get(key, [])
        asset = Asset(
            organization_id=current_user.organization_id,
            created_by_user_id=current_user.id,
            host=discovered.host,
            port=discovered.port,
            service=discovered.service,
            tls_valid=discovered.tls_valid,
            oauth_scope_excessive=discovered.oauth_scope_excessive,
            risk_findings=[f.model_dump(mode="json") for f in risk_findings],
        )
        db.add(asset)
        created.append(asset)

    await db.commit()
    for asset in created:
        await db.refresh(asset)

    await connection_manager.broadcast(
        current_user.organization_id,
        {
            "agent": "attack_surface_recon",
            "status": "completed",
            "domain": payload.domain,
            "assets_found": len(created),
            "risk_score": assessment.overall_risk_score,
        },
    )

    return created
