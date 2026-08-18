from pydantic import BaseModel, Field


class DiscoveredAsset(BaseModel):
    """A passively observed asset from recon (DNS, ports, TLS, OAuth grants)."""

    host: str
    port: int | None = None
    service: str | None = None
    tls_valid: bool | None = None
    oauth_scope_excessive: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)
