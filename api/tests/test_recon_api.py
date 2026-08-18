from app.agents.recon_agent import AttackSurfaceReconAgent
from app.api.v1.recon import get_recon_agent
from app.main import app
from app.schemas.asset import DiscoveredAsset
from app.schemas.recon import ReconResult


class _FakeReconAgent:
    def __init__(self, assets):
        self._assets = assets

    async def scan(self, domain: str) -> ReconResult:
        return ReconResult(domain=domain, resolved_ip="93.184.216.34", assets=self._assets)


class _FailingReconAgent:
    async def scan(self, domain: str) -> ReconResult:
        raise RuntimeError("DNS timed out")


def test_scan_persists_discovered_assets_with_risk_findings(client, auth_headers):
    fake_assets = [DiscoveredAsset(host="example.org", port=3389, service="rdp")]
    app.dependency_overrides[get_recon_agent] = lambda: _FakeReconAgent(fake_assets)
    try:
        response = client.post(
            "/api/v1/recon/scan", headers=auth_headers, json={"domain": "example.org"}
        )
    finally:
        app.dependency_overrides.pop(get_recon_agent, None)

    assert response.status_code == 201
    body = response.json()
    assert len(body) == 1
    assert body[0]["host"] == "example.org"
    assert body[0]["risk_findings"][0]["technique_id"] == "T1021.001"


def test_scan_failure_returns_503_without_leaking_internals(client, auth_headers):
    app.dependency_overrides[get_recon_agent] = lambda: _FailingReconAgent()
    try:
        response = client.post(
            "/api/v1/recon/scan", headers=auth_headers, json={"domain": "example.org"}
        )
    finally:
        app.dependency_overrides.pop(get_recon_agent, None)

    assert response.status_code == 503
    assert "DNS timed out" not in response.text


def test_scanned_assets_are_visible_to_teammates(client, auth_headers):
    fake_assets = [DiscoveredAsset(host="shared.example.org")]
    app.dependency_overrides[get_recon_agent] = lambda: _FakeReconAgent(fake_assets)
    try:
        client.post("/api/v1/recon/scan", headers=auth_headers, json={"domain": "shared.example.org"})
    finally:
        app.dependency_overrides.pop(get_recon_agent, None)

    response = client.get("/api/v1/assets", headers=auth_headers)

    hosts = [a["host"] for a in response.json()]
    assert "shared.example.org" in hosts


def test_scan_requires_auth(client):
    response = client.post("/api/v1/recon/scan", json={"domain": "example.org"})

    assert response.status_code == 401


def test_get_recon_agent_returns_real_agent():
    assert isinstance(get_recon_agent(), AttackSurfaceReconAgent)
