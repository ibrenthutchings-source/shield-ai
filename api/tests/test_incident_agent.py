from app.agents.incident_agent import IncidentResponderAgent
from app.schemas.incident import IncidentContext, IncidentPhaseName, PlaybookPhase


def _fake_generator_factory():
    call_order: list[IncidentPhaseName] = []

    def fake_generator(phase: IncidentPhaseName, context: IncidentContext) -> PlaybookPhase:
        call_order.append(phase)
        return PlaybookPhase(
            phase=phase,
            executive_summary=f"Executive summary for {phase.value} of {context.incident_type}.",
            technical_steps=[f"Step for {phase.value}"],
            commands=[f"echo {phase.value}"],
        )

    return fake_generator, call_order


def test_playbook_runs_phases_in_order():
    fake_generator, call_order = _fake_generator_factory()
    agent = IncidentResponderAgent(phase_generator=fake_generator)

    context = IncidentContext(
        incident_type="Ransomware",
        affected_systems=["fileserver01"],
        environment="Azure",
        description="Encrypted shares detected overnight.",
    )
    playbook = agent.run(context)

    assert call_order == [
        IncidentPhaseName.TRIAGE,
        IncidentPhaseName.FORENSICS,
        IncidentPhaseName.RECOVERY,
    ]
    assert [p.phase for p in playbook.phases] == call_order
    assert playbook.incident_type == "Ransomware"


def test_each_phase_has_dual_audience_output():
    fake_generator, _ = _fake_generator_factory()
    agent = IncidentResponderAgent(phase_generator=fake_generator)

    playbook = agent.run(IncidentContext(incident_type="Phishing"))

    for phase in playbook.phases:
        assert phase.executive_summary
        assert phase.technical_steps
        assert phase.commands


def test_generator_receives_the_incident_context():
    seen_contexts: list[IncidentContext] = []

    def fake_generator(phase: IncidentPhaseName, context: IncidentContext) -> PlaybookPhase:
        seen_contexts.append(context)
        return PlaybookPhase(phase=phase, executive_summary="x", technical_steps=["x"])

    agent = IncidentResponderAgent(phase_generator=fake_generator)
    context = IncidentContext(incident_type="OAuth Tenant Hijacking", environment="Google Workspace")
    agent.run(context)

    assert len(seen_contexts) == 3
    assert all(c == context for c in seen_contexts)


def test_default_generator_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    from app.core.config import get_settings

    get_settings.cache_clear()

    agent = IncidentResponderAgent()

    try:
        agent.run(IncidentContext(incident_type="Ransomware"))
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "ANTHROPIC_API_KEY" in str(exc)
