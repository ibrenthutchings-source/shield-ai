from app.agents.incident_agent import IncidentResponderAgent
from app.api.v1.deps import get_incident_agent
from app.main import app
from app.schemas.incident import IncidentContext, IncidentPhaseName, PlaybookPhase


class _FakeIncidentAgent:
    def run(self, context: IncidentContext):
        return IncidentResponderAgent(phase_generator=self._fake_generator).run(context)

    @staticmethod
    def _fake_generator(phase: IncidentPhaseName, context: IncidentContext) -> PlaybookPhase:
        return PlaybookPhase(
            phase=phase,
            executive_summary=f"Executive summary for {phase.value}.",
            technical_steps=[f"Technical step for {phase.value}"],
            commands=["Get-MgUser -UserId user@example.com"],
        )


class _FailingIncidentAgent:
    def run(self, context: IncidentContext):
        raise RuntimeError("ANTHROPIC_API_KEY is required to generate incident playbooks")


def test_create_incident_returns_generated_playbook(client, auth_headers):
    app.dependency_overrides[get_incident_agent] = lambda: _FakeIncidentAgent()
    try:
        response = client.post(
            "/api/v1/incidents",
            headers=auth_headers,
            json={
                "incident_type": "Ransomware",
                "affected_systems": ["fileserver01"],
                "environment": "Azure",
                "description": "Encrypted shares overnight.",
            },
        )
    finally:
        app.dependency_overrides.pop(get_incident_agent, None)

    assert response.status_code == 201
    body = response.json()
    assert body["incident_type"] == "Ransomware"
    assert body["status"] == "in_progress"
    assert len(body["playbook"]["phases"]) == 3


def test_create_incident_failure_returns_503_without_leaking_internals(client, auth_headers):
    app.dependency_overrides[get_incident_agent] = lambda: _FailingIncidentAgent()
    try:
        response = client.post(
            "/api/v1/incidents",
            headers=auth_headers,
            json={"incident_type": "Ransomware"},
        )
    finally:
        app.dependency_overrides.pop(get_incident_agent, None)

    assert response.status_code == 503
    assert "ANTHROPIC_API_KEY" not in response.text


def test_list_incidents_scoped_to_current_user(client, auth_headers):
    app.dependency_overrides[get_incident_agent] = lambda: _FakeIncidentAgent()
    try:
        client.post(
            "/api/v1/incidents",
            headers=auth_headers,
            json={"incident_type": "Phishing"},
        )
    finally:
        app.dependency_overrides.pop(get_incident_agent, None)

    response = client.get("/api/v1/incidents", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["incident_type"] == "Phishing"


def test_get_incident_not_found(client, auth_headers):
    response = client.get(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )

    assert response.status_code == 404
