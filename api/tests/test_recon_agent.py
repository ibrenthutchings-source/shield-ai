import httpx
import pytest

from app.agents.recon_agent import AttackSurfaceReconAgent


async def _resolve_stub(domain: str) -> str | None:
    return "93.184.216.34"


async def _no_resolve(domain: str) -> str | None:
    return None


async def _tls_valid(domain: str) -> bool:
    return True


async def _tls_invalid(domain: str) -> bool:
    return False


def _mock_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_scan_returns_https_asset_with_tls_result():
    agent = AttackSurfaceReconAgent(resolve=_resolve_stub, check_tls=_tls_valid)

    result = await agent.scan("example.org")

    assert result.resolved_ip == "93.184.216.34"
    https_assets = [a for a in result.assets if a.service == "https"]
    assert len(https_assets) == 1
    assert https_assets[0].tls_valid is True


async def test_scan_reports_invalid_tls():
    agent = AttackSurfaceReconAgent(resolve=_resolve_stub, check_tls=_tls_invalid)

    result = await agent.scan("example.org")

    assert result.assets[0].tls_valid is False


async def test_scan_skips_tls_check_when_dns_resolution_fails():
    agent = AttackSurfaceReconAgent(resolve=_no_resolve, check_tls=_tls_valid)

    result = await agent.scan("nonexistent.invalid")

    assert result.resolved_ip is None
    assert result.assets[0].tls_valid is None


async def test_scan_skips_shodan_and_censys_without_api_keys(monkeypatch):
    monkeypatch.delenv("SHODAN_API_KEY", raising=False)
    monkeypatch.delenv("CENSYS_API_ID", raising=False)
    monkeypatch.delenv("CENSYS_API_SECRET", raising=False)
    from app.core.config import get_settings

    get_settings.cache_clear()

    agent = AttackSurfaceReconAgent(resolve=_resolve_stub, check_tls=_tls_valid)
    result = await agent.scan("example.org")

    # Only the baseline https entry, since no scan-database keys are configured.
    assert len(result.assets) == 1


async def test_scan_includes_shodan_ports_when_configured(monkeypatch):
    monkeypatch.setenv("SHODAN_API_KEY", "test-key")
    monkeypatch.delenv("CENSYS_API_ID", raising=False)
    monkeypatch.delenv("CENSYS_API_SECRET", raising=False)
    from app.core.config import get_settings

    get_settings.cache_clear()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["key"] == "test-key"
        return httpx.Response(
            200,
            json={"data": [{"port": 3389, "transport": "tcp", "_shodan": {"module": "rdp"}}]},
        )

    async with _mock_client(handler) as client:
        agent = AttackSurfaceReconAgent(http_client=client, resolve=_resolve_stub, check_tls=_tls_valid)
        result = await agent.scan("example.org")

    rdp_assets = [a for a in result.assets if a.port == 3389]
    assert len(rdp_assets) == 1
    assert rdp_assets[0].service == "rdp"


async def test_scan_handles_shodan_http_error_gracefully(monkeypatch):
    monkeypatch.setenv("SHODAN_API_KEY", "test-key")
    monkeypatch.delenv("CENSYS_API_ID", raising=False)
    monkeypatch.delenv("CENSYS_API_SECRET", raising=False)
    from app.core.config import get_settings

    get_settings.cache_clear()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    async with _mock_client(handler) as client:
        agent = AttackSurfaceReconAgent(http_client=client, resolve=_resolve_stub, check_tls=_tls_valid)
        result = await agent.scan("example.org")

    # Baseline https entry still returned even though Shodan failed.
    assert len(result.assets) == 1


async def test_scan_includes_censys_services_when_configured(monkeypatch):
    monkeypatch.delenv("SHODAN_API_KEY", raising=False)
    monkeypatch.setenv("CENSYS_API_ID", "test-id")
    monkeypatch.setenv("CENSYS_API_SECRET", "test-secret")
    from app.core.config import get_settings

    get_settings.cache_clear()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"result": {"services": [{"port": 25, "service_name": "SMTP"}]}},
        )

    async with _mock_client(handler) as client:
        agent = AttackSurfaceReconAgent(http_client=client, resolve=_resolve_stub, check_tls=_tls_valid)
        result = await agent.scan("example.org")

    smtp_assets = [a for a in result.assets if a.port == 25]
    assert len(smtp_assets) == 1
    assert smtp_assets[0].service == "SMTP"
