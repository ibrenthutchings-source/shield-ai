from pydantic import BaseModel, Field

from app.schemas.asset import DiscoveredAsset


class ReconTarget(BaseModel):
    domain: str


class ReconResult(BaseModel):
    domain: str
    resolved_ip: str | None
    assets: list[DiscoveredAsset] = Field(default_factory=list)
