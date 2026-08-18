from app.agents.redteam_agent import RedTeamSimulationAgent
from app.schemas.asset import DiscoveredAsset


def test_open_rdp_maps_to_lateral_movement_technique():
    agent = RedTeamSimulationAgent()
    asset = DiscoveredAsset(host="host1.example.org", port=3389, service="rdp")

    result = agent.assess([asset])

    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.technique_id == "T1021.001"
    assert finding.tactic == "Lateral Movement"
    assert finding.severity == "high"


def test_excessive_oauth_scope_maps_to_credential_access_technique():
    agent = RedTeamSimulationAgent()
    asset = DiscoveredAsset(host="tenant.example.org", oauth_scope_excessive=True)

    result = agent.assess([asset])

    assert len(result.findings) == 1
    assert result.findings[0].technique_id == "T1528"
    assert result.findings[0].severity == "critical"


def test_asset_matching_no_rules_produces_no_findings():
    agent = RedTeamSimulationAgent()
    asset = DiscoveredAsset(host="benign.example.org", port=443, service="https", tls_valid=True)

    result = agent.assess([asset])

    assert result.findings == []
    assert result.overall_risk_score == 0.0


def test_asset_can_trigger_multiple_technique_mappings():
    agent = RedTeamSimulationAgent()
    asset = DiscoveredAsset(
        host="mail.example.org",
        service="smtp",
        tls_valid=False,
    )

    result = agent.assess([asset])

    technique_ids = {f.technique_id for f in result.findings}
    assert technique_ids == {"T1566", "T1557"}


def test_overall_risk_score_is_average_of_severity_weights():
    agent = RedTeamSimulationAgent()
    assets = [
        DiscoveredAsset(host="a.example.org", port=3389),  # high -> 75
        DiscoveredAsset(host="b.example.org", oauth_scope_excessive=True),  # critical -> 100
    ]

    result = agent.assess(assets)

    assert result.overall_risk_score == (75 + 100) / 2


def test_no_active_exploitation_only_passive_classification():
    # Guardrail: the agent's public surface is a pure classifier over
    # already-observed asset data, with no method that sends network traffic.
    agent = RedTeamSimulationAgent()
    public_methods = [name for name in dir(agent) if not name.startswith("_")]

    assert public_methods == ["assess"]
