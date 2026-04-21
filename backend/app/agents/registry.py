"""Central registry of all specialist agents."""
from __future__ import annotations

from threading import RLock
from typing import Any

from app.core.logging import get_logger
from app.governance.autonomy import autonomy_registry
from app.models.schemas import AgentDescriptor

log = get_logger(__name__)


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, Any] = {}
        self._lock = RLock()

    def register(self, agent: Any) -> None:
        with self._lock:
            self._agents[agent.descriptor.name] = agent
        autonomy_registry.get(agent.descriptor.name).level = (
            agent.descriptor.autonomy_level
        )
        log.info("agent.registered", name=agent.descriptor.name)

    def get(self, name: str) -> Any:
        return self._agents[name]

    def list(self) -> list[AgentDescriptor]:
        return [a.descriptor for a in self._agents.values()]

    def all(self) -> list[Any]:
        return list(self._agents.values())


agent_registry = AgentRegistry()


def register_all_agents() -> None:
    """Instantiate and register the full agent roster.

    Add new agents here — the registry becomes the canonical list.
    """
    from app.agents.capacity_agent import CapacityAgent
    from app.agents.change_risk_agent import ChangeRiskAgent
    from app.agents.correlation_agent import CorrelationAgent
    from app.agents.incident_commander import IncidentCommanderAgent
    from app.agents.kedb_agent import KEDBAgent
    from app.agents.pir_agent import PIRAgent
    from app.agents.rca_agent import RCAAgent
    from app.agents.release_agent import ReleaseAgent
    from app.agents.remediation_agent import RemediationAgent
    from app.agents.slo_agent import SLOAgent
    from app.agents.triage_agent import TriageAgent

    for cls in (
        TriageAgent,
        CorrelationAgent,
        IncidentCommanderAgent,
        RCAAgent,
        RemediationAgent,
        PIRAgent,
        KEDBAgent,
        ChangeRiskAgent,
        ReleaseAgent,
        SLOAgent,
        CapacityAgent,
    ):
        agent_registry.register(cls())
