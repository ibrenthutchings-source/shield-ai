from collections.abc import Callable
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.schemas.incident import IncidentContext, IncidentPhaseName, IncidentPlaybook, PlaybookPhase

PhaseGenerator = Callable[[IncidentPhaseName, IncidentContext], PlaybookPhase]


class IncidentState(TypedDict):
    context: IncidentContext
    phases: list[PlaybookPhase]


def _default_phase_generator(phase: IncidentPhaseName, context: IncidentContext) -> PlaybookPhase:
    """Generates one playbook phase via the configured frontier LLM (LangGraph node).

    Uses `with_structured_output` (Anthropic tool-calling under the hood) rather
    than asking the model to emit raw JSON text — the latter is brittle against
    newer Claude models, which often wrap JSON in prose or markdown fences that
    a plain text parser can't handle.
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.prompts import ChatPromptTemplate

    from app.core.config import get_settings

    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is required to generate incident playbooks")

    llm = ChatAnthropic(model="claude-sonnet-5", api_key=settings.anthropic_api_key)
    structured_llm = llm.with_structured_output(PlaybookPhase)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are ShieldAI's incident response planner for lean IT teams at schools "
                "and non-profits. Produce the '{phase}' phase of a containment playbook with "
                "an Executive Summary (plain business language) and Technical Remediation "
                "steps including executable Azure CLI / PowerShell / Google Workspace "
                "commands.",
            ),
            (
                "human",
                "Incident type: {incident_type}\nAffected systems: {affected_systems}\n"
                "Environment: {environment}\nDescription: {description}",
            ),
        ]
    )

    chain = prompt | structured_llm
    result = chain.invoke(
        {
            "phase": phase.value,
            "incident_type": context.incident_type,
            "affected_systems": ", ".join(context.affected_systems) or "unspecified",
            "environment": context.environment,
            "description": context.description or "unspecified",
        }
    )
    # The model fills in `phase` itself; pin it to the value we actually
    # requested rather than trust its fidelity to the prompt.
    return result.model_copy(update={"phase": phase})


def build_incident_graph(phase_generator: PhaseGenerator | None = None):
    generator = phase_generator or _default_phase_generator

    def _make_node(phase: IncidentPhaseName):
        def _node(state: IncidentState) -> dict:
            result = generator(phase, state["context"])
            return {"phases": [*state["phases"], result]}

        return _node

    graph = StateGraph(IncidentState)
    graph.add_node("triage", _make_node(IncidentPhaseName.TRIAGE))
    graph.add_node("forensics", _make_node(IncidentPhaseName.FORENSICS))
    graph.add_node("recovery", _make_node(IncidentPhaseName.RECOVERY))

    graph.set_entry_point("triage")
    graph.add_edge("triage", "forensics")
    graph.add_edge("forensics", "recovery")
    graph.add_edge("recovery", END)

    return graph.compile()


class IncidentResponderAgent:
    """LangGraph state machine producing a 3-phase containment playbook.

    The LLM call per phase is injected (`phase_generator`) so the graph
    topology can be tested without a live Anthropic/OpenAI key; production
    use falls back to a real Claude call via `_default_phase_generator`.
    """

    def __init__(self, phase_generator: PhaseGenerator | None = None):
        self._graph = build_incident_graph(phase_generator)

    def run(self, context: IncidentContext) -> IncidentPlaybook:
        result = self._graph.invoke({"context": context, "phases": []})
        return IncidentPlaybook(incident_type=context.incident_type, phases=result["phases"])
