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

    The Supervisor only wires a subset into its LangGraph flow; all
    other agents are runnable independently via `/api/agents/{name}/run`
    and surface in the console Agent Roster + Governance views.
    """
    # Phase 1 — Incident core
    from app.agents.correlation_agent import CorrelationAgent
    from app.agents.incident_commander import IncidentCommanderAgent
    from app.agents.kedb_agent import KEDBAgent
    from app.agents.pir_agent import PIRAgent
    from app.agents.rca_agent import RCAAgent
    from app.agents.remediation_agent import RemediationAgent
    from app.agents.triage_agent import TriageAgent

    # Phase 2 — Release & Change
    from app.agents.cab_agent import CABAgent
    from app.agents.canary_agent import CanaryAgent
    from app.agents.change_risk_agent import ChangeRiskAgent
    from app.agents.deployment_drift_agent import DeploymentDriftAgent
    from app.agents.feature_flag_agent import FeatureFlagGovernanceAgent
    from app.agents.release_agent import ReleaseAgent
    from app.agents.release_notes_agent import ReleaseNotesAgent
    from app.agents.rollback_agent import RollbackAgent

    # Phase 3 — SRE
    from app.agents.capacity_agent import CapacityAgent
    from app.agents.slo_agent import SLOAgent
    from app.agents.sre_agents import (
        ChaosAgent,
        DependencyMappingAgent,
        ObservabilityCoverageAgent,
        ReliabilityScoreAgent,
        RunbookAuthoringAgent,
        ToilDetectionAgent,
    )

    # Phase 3 — Hardware
    from app.agents.hardware_agents import (
        DiskFailurePredictionAgent,
        FirmwareLifecycleAgent,
        HardwareHealthAgent,
        NetworkFabricAgent,
        PowerThermalAgent,
    )

    # Phase 3 — Platform
    from app.agents.platform_agents import (
        BackupDRAgent,
        CertificateAgent,
        CloudOptimizerAgent,
        IaCDriftAgent,
        NetworkPolicyAgent,
        OSPatchingAgent,
        StorageAgent,
    )

    # Phase 3 — Middleware
    from app.agents.middleware_agents import (
        APIGatewayAgent,
        CacheAgent,
        ContainerRuntimeAgent,
        DBAAgent,
        LoadBalancerAgent,
        MessageBrokerAgent,
        ServiceMeshAgent,
    )

    # Phase 3 — Application
    from app.agents.application_agents import (
        APMAgent,
        DistributedTraceAgent,
        FeaturePerformanceAgent,
        LogAnalysisAgent,
        RUMAgent,
        SessionReplayAgent,
        SyntheticAgent,
    )

    # Phase 4 — Analytics / Predictive / Security / Governance
    from app.agents.phase4_agents import (
        ComplianceAgent,
        DocumentationAgent,
        FinOpsAgent,
        KGMaintenanceAgent,
        MajorIncidentPredictorAgent,
        SecurityCorrelationAgent,
    )

    for cls in (
        # Phase 1
        TriageAgent, CorrelationAgent, IncidentCommanderAgent, RCAAgent,
        RemediationAgent, PIRAgent, KEDBAgent,
        # Phase 2
        ChangeRiskAgent, CABAgent, CanaryAgent, RollbackAgent, ReleaseAgent,
        ReleaseNotesAgent, FeatureFlagGovernanceAgent, DeploymentDriftAgent,
        # Phase 3 — SRE
        SLOAgent, CapacityAgent, ToilDetectionAgent, ChaosAgent,
        DependencyMappingAgent, ReliabilityScoreAgent, RunbookAuthoringAgent,
        ObservabilityCoverageAgent,
        # Phase 3 — Hardware
        HardwareHealthAgent, DiskFailurePredictionAgent, FirmwareLifecycleAgent,
        NetworkFabricAgent, PowerThermalAgent,
        # Phase 3 — Platform
        CloudOptimizerAgent, IaCDriftAgent, OSPatchingAgent, StorageAgent,
        NetworkPolicyAgent, CertificateAgent, BackupDRAgent,
        # Phase 3 — Middleware
        DBAAgent, MessageBrokerAgent, APIGatewayAgent, ServiceMeshAgent,
        CacheAgent, ContainerRuntimeAgent, LoadBalancerAgent,
        # Phase 3 — Application
        APMAgent, LogAnalysisAgent, DistributedTraceAgent, RUMAgent,
        SyntheticAgent, FeaturePerformanceAgent, SessionReplayAgent,
        # Phase 4
        MajorIncidentPredictorAgent, FinOpsAgent, ComplianceAgent,
        SecurityCorrelationAgent, KGMaintenanceAgent, DocumentationAgent,
    ):
        agent_registry.register(cls())
