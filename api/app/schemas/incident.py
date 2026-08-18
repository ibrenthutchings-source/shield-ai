from enum import Enum

from pydantic import BaseModel, Field


class IncidentPhaseName(str, Enum):
    TRIAGE = "emergency_triage"
    FORENSICS = "forensics"
    RECOVERY = "recovery"


class IncidentContext(BaseModel):
    incident_type: str
    affected_systems: list[str] = Field(default_factory=list)
    environment: str = "Google Workspace"
    description: str = ""


class PlaybookPhase(BaseModel):
    phase: IncidentPhaseName
    executive_summary: str
    technical_steps: list[str]
    commands: list[str] = Field(default_factory=list)


class IncidentPlaybook(BaseModel):
    incident_type: str
    phases: list[PlaybookPhase]
