import asyncio
import logging
import socket
import ssl
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

import httpx

from app.core.config import get_settings
from app.schemas.asset import DiscoveredAsset
from app.schemas.recon import ReconResult

logger = logging.getLogger(__name__)

_TLS_PORT = 443
_TLS_HANDSHAKE_TIMEOUT = 5.0
_HTTP_TIMEOUT = 10.0

Resolver = Callable[[str], Awaitable[str | None]]
TlsChecker = Callable[[str], Awaitable[bool | None]]


class AttackSurfaceReconAgent:
    """Passively audits a domain's public footprint.

    Resolves DNS, checks TLS certificate validity via a standard handshake,
    and — only when API keys are configured — pulls open-port/service data
    from Shodan and Censys, internet-wide scan databases that have already
    indexed the target. This agent never scans ports itself and sends no
    exploit traffic; DNS resolution and a TLS handshake are the only network
    activity, matching how any browser or `curl` would reach the same host.

    DNS resolution and the TLS check are injectable so this is unit-testable
    without touching the network, following the same pattern as
    `IncidentResponderAgent`'s injectable phase generator.
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        resolve: Resolver | None = None,
        check_tls: TlsChecker | None = None,
    ):
        self._client = http_client
        self._resolve = resolve or self._default_resolve
        self._check_tls = check_tls or self._default_check_tls

    async def scan(self, domain: str) -> ReconResult:
        resolved_ip = await self._resolve(domain)
        tls_valid = await self._check_tls(domain) if resolved_ip else None

        assets: list[DiscoveredAsset] = [
            DiscoveredAsset(host=domain, port=_TLS_PORT, service="https", tls_valid=tls_valid)
        ]

        if resolved_ip:
            assets.extend(await self._shodan_assets(domain, resolved_ip))
            assets.extend(await self._censys_assets(domain, resolved_ip))

        return ReconResult(domain=domain, resolved_ip=resolved_ip, assets=assets)

    @asynccontextmanager
    async def _http_client(self):
        if self._client is not None:
            yield self._client
            return
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            yield client

    async def _shodan_assets(self, domain: str, ip: str) -> list[DiscoveredAsset]:
        settings = get_settings()
        if not settings.shodan_api_key:
            return []

        try:
            async with self._http_client() as client:
                response = await client.get(
                    f"https://api.shodan.io/shodan/host/{ip}",
                    params={"key": settings.shodan_api_key},
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError:
            logger.exception("Shodan lookup failed for %s (%s)", domain, ip)
            return []

        return [
            DiscoveredAsset(
                host=domain,
                port=item.get("port"),
                service=(item.get("_shodan") or {}).get("module") or item.get("transport"),
            )
            for item in data.get("data", [])
        ]

    async def _censys_assets(self, domain: str, ip: str) -> list[DiscoveredAsset]:
        settings = get_settings()
        if not (settings.censys_api_id and settings.censys_api_secret):
            return []

        try:
            async with self._http_client() as client:
                response = await client.get(
                    f"https://search.censys.io/api/v2/hosts/{ip}",
                    auth=(settings.censys_api_id, settings.censys_api_secret),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError:
            logger.exception("Censys lookup failed for %s (%s)", domain, ip)
            return []

        return [
            DiscoveredAsset(host=domain, port=service.get("port"), service=service.get("service_name"))
            for service in ((data.get("result") or {}).get("services") or [])
        ]

    @staticmethod
    async def _default_resolve(domain: str) -> str | None:
        loop = asyncio.get_event_loop()
        try:
            infos = await loop.getaddrinfo(domain, None, family=socket.AF_INET)
        except socket.gaierror:
            logger.info("DNS resolution failed for %s", domain)
            return None
        return infos[0][4][0] if infos else None

    @staticmethod
    async def _default_check_tls(domain: str) -> bool:
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, AttackSurfaceReconAgent._blocking_tls_handshake, domain),
                timeout=_TLS_HANDSHAKE_TIMEOUT,
            )
            return True
        except (ssl.SSLError, OSError, asyncio.TimeoutError):
            return False

    @staticmethod
    def _blocking_tls_handshake(domain: str) -> None:
        context = ssl.create_default_context()
        with socket.create_connection((domain, _TLS_PORT), timeout=_TLS_HANDSHAKE_TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=domain):
                pass
