import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IncidentCreateRequest(BaseModel):
    incident_type: str
    affected_systems: list[str] = Field(default_factory=list)
    environment: str = "Google Workspace"
    description: str = ""


class IncidentRead(BaseModel):
    id: uuid.UUID
    incident_type: str
    environment: str
    description: str
    status: str
    playbook: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
