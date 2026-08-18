import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssetRead(BaseModel):
    id: uuid.UUID
    host: str
    port: int | None
    service: str | None
    tls_valid: bool | None
    oauth_scope_excessive: bool
    risk_findings: list[dict] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
