from pydantic import BaseModel

from app.schemas.asset import DiscoveredAsset

Severity = str  # "low" | "medium" | "high" | "critical"


class TechniqueMapping(BaseModel):
    asset: DiscoveredAsset
    technique_id: str
    technique_name: str
    tactic: str
    severity: Severity
    executive_summary: str
    technical_remediation: list[str]


class RiskAssessment(BaseModel):
    findings: list[TechniqueMapping]
    overall_risk_score: float
