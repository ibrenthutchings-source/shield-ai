import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.agents.incident_agent import IncidentResponderAgent
from app.api.v1.deps import get_current_user, get_incident_agent
from app.db.session import get_db
from app.models.incident import Incident
from app.models.user import User
from app.schemas.incident import IncidentContext
from app.schemas.incident_api import IncidentCreateRequest, IncidentRead
from app.ws.connection_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
async def create_incident(
    payload: IncidentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agent: IncidentResponderAgent = Depends(get_incident_agent),
) -> Incident:
    await connection_manager.broadcast(
        current_user.organization_id,
        {"agent": "incident_responder", "status": "started", "incident_type": payload.incident_type},
    )

    context = IncidentContext(
        incident_type=payload.incident_type,
        affected_systems=payload.affected_systems,
        environment=payload.environment,
        description=payload.description,
    )

    try:
        playbook = await run_in_threadpool(agent.run, context)
    except Exception:
        logger.exception("Incident playbook generation failed for %s", payload.incident_type)
        await connection_manager.broadcast(
            current_user.organization_id,
            {"agent": "incident_responder", "status": "error", "incident_type": payload.incident_type},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Incident playbook generation is temporarily unavailable",
        )

    incident = Incident(
        organization_id=current_user.organization_id,
        created_by_user_id=current_user.id,
        incident_type=payload.incident_type,
        environment=payload.environment,
        description=payload.description,
        status="in_progress",
        playbook=playbook.model_dump(mode="json"),
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)

    await connection_manager.broadcast(
        current_user.organization_id,
        {"agent": "incident_responder", "status": "completed", "incident_id": str(incident.id)},
    )

    return incident


@router.get("", response_model=list[IncidentRead])
async def list_incidents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Incident]:
    result = await db.execute(
        select(Incident)
        .where(Incident.organization_id == current_user.organization_id)
        .order_by(Incident.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Incident:
    result = await db.execute(
        select(Incident).where(
            Incident.id == incident_id, Incident.organization_id == current_user.organization_id
        )
    )
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident
