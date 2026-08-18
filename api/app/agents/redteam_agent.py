from collections.abc import Callable
from dataclasses import dataclass

from app.schemas.asset import DiscoveredAsset
from app.schemas.redteam import RiskAssessment, TechniqueMapping

_SEVERITY_WEIGHT = {"low": 25, "medium": 50, "high": 75, "critical": 100}


@dataclass(frozen=True)
class _Rule:
    matches: Callable[[DiscoveredAsset], bool]
    technique_id: str
    technique_name: str
    tactic: str
    severity: str
    executive_summary: str
    technical_remediation: list[str]


_RULES: list[_Rule] = [
    _Rule(
        matches=lambda a: a.port == 3389,
        technique_id="T1021.001",
        technique_name="Remote Desktop Protocol",
        tactic="Lateral Movement",
        severity="high",
        executive_summary=(
            "A remote desktop login is reachable from the public internet, giving an "
            "attacker a direct path into internal systems if they guess or steal a password."
        ),
        technical_remediation=[
            "Restrict inbound RDP (3389) to the VPN/private network via network security group rules.",
            "Enable Network Level Authentication and MFA for all RDP sessions.",
        ],
    ),
    _Rule(
        matches=lambda a: (a.service or "").lower() == "smtp",
        technique_id="T1566",
        technique_name="Phishing",
        tactic="Initial Access",
        severity="medium",
        executive_summary=(
            "The mail server is exposed without evidence of anti-spoofing controls, making "
            "it easier for attackers to send convincing phishing emails impersonating this domain."
        ),
        technical_remediation=[
            "Publish SPF, DKIM, and DMARC (p=reject) records for the domain.",
            "Enable inbound phishing/attachment scanning at the mail gateway.",
        ],
    ),
    _Rule(
        matches=lambda a: a.oauth_scope_excessive,
        technique_id="T1528",
        technique_name="Steal Application Access Token (OAuth Tenant Hijacking)",
        tactic="Credential Access",
        severity="critical",
        executive_summary=(
            "A connected third-party app has broader account permissions than it needs. If "
            "that app is compromised, an attacker inherits its access without ever needing a password."
        ),
        technical_remediation=[
            "Review and revoke excessive OAuth grants in the admin console (Google Workspace: "
            "Security > API Controls; Microsoft 365: Enterprise Applications > Permissions).",
            "Restrict future app installs to an admin-approved allowlist.",
        ],
    ),
    _Rule(
        matches=lambda a: a.tls_valid is False,
        technique_id="T1557",
        technique_name="Adversary-in-the-Middle",
        tactic="Credential Access",
        severity="medium",
        executive_summary=(
            "This service presents an invalid or expired TLS certificate, so visitors' "
            "browsers can't verify they're really talking to your server — an opening for "
            "traffic interception."
        ),
        technical_remediation=[
            "Reissue and install a valid certificate (e.g. via Let's Encrypt or your CA).",
            "Enable automatic certificate renewal to prevent recurrence.",
        ],
    ),
]


class RedTeamSimulationAgent:
    """Maps passively discovered assets to MITRE ATT&CK techniques and scores risk exposure.

    This never runs active exploits — it only classifies conditions recon already
    observed (open ports, service banners, TLS state, OAuth grants) against a
    rule table of known technique preconditions.
    """

    def assess(self, assets: list[DiscoveredAsset]) -> RiskAssessment:
        findings: list[TechniqueMapping] = []

        for asset in assets:
            for rule in _RULES:
                if rule.matches(asset):
                    findings.append(
                        TechniqueMapping(
                            asset=asset,
                            technique_id=rule.technique_id,
                            technique_name=rule.technique_name,
                            tactic=rule.tactic,
                            severity=rule.severity,
                            executive_summary=rule.executive_summary,
                            technical_remediation=rule.technical_remediation,
                        )
                    )

        overall_risk_score = (
            sum(_SEVERITY_WEIGHT[f.severity] for f in findings) / len(findings) if findings else 0.0
        )

        return RiskAssessment(findings=findings, overall_risk_score=overall_risk_score)
