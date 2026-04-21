"""SRE specialist agents — Toil, Chaos, DependencyMap, ReliabilityScore,
RunbookAuthoring, ObservabilityCoverage.

Kept together because they share the same KG + observability inputs.
"""
from __future__ import annotations

from typing import Any

from app.agents.base import AgentBase, AgentState
from app.kg.neo4j_client import kg
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


# -----------------------------------------------------------------------------
# Toil Detection — find repetitive manual operations worth automating.
# -----------------------------------------------------------------------------


class ToilDetectionAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="toil-agent",
        display_name="Toil Detection",
        workstream="sre",
        description="Mine ticket + chat trails for repetitive manual ops; propose automation.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-itsm.search_kedb", "mcp-knowledge.search_confluence"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-knowledge.search_confluence", args={"query": "runbook"}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        candidates = [
            {"task": "restart orders-db long sessions", "monthly_count": 18, "est_min_each": 12},
            {"task": "rotate stale secrets", "monthly_count": 9, "est_min_each": 25},
        ]
        toil_hours = sum(c["monthly_count"] * c["est_min_each"] / 60 for c in candidates)
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Estimated {toil_hours:.1f} toil hours/month — {len(candidates)} automatable tasks.",
            action="propose_automations",
            tool_calls=[],
            confidence=0.72,
            evidence=[EvidenceItem(source="toil-mining", kind="metric", payload={"candidates": candidates})],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


# -----------------------------------------------------------------------------
# Chaos Agent — plans and supervises chaos experiments.
# -----------------------------------------------------------------------------


class ChaosAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="chaos-agent",
        display_name="Chaos Engineering",
        workstream="sre",
        description="Plan and run controlled chaos experiments with safety rails.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-k8s.cordon", "mcp-k8s.drain", "mcp-observability.query_metrics"],
        blast_radius={"max_services": 1},
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        target = state["input"].get("target", "checkout")
        experiment = state["input"].get("experiment", "kill-one-pod")
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Chaos experiment {experiment} scoped to {target}, blast radius = 1 pod.",
            action="run_experiment",
            tool_calls=[],
            confidence=0.68,
            evidence=[EvidenceItem(source="plan", kind="change",
                                   payload={"experiment": experiment, "target": target, "stop_on": "error_rate>0.02"})],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


# -----------------------------------------------------------------------------
# Dependency Mapping — keeps the live service catalog from traces + IaC.
# -----------------------------------------------------------------------------


class DependencyMappingAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="dependency-map-agent",
        display_name="Dependency Mapping",
        workstream="sre",
        description="Maintain live dependency map from traces; update KG.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-observability.get_traces"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-observability.get_traces", args={"service": "checkout", "limit": 20}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        services = await kg.all_services()
        edges = len([n for n in services if n.get("name")])
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Dependency map refreshed — {len(services)} services, {edges} edges.",
            action="update_kg",
            tool_calls=[],
            confidence=0.8,
            evidence=[EvidenceItem(source="traces", kind="metric", payload={"nodes": len(services)})],
            requires_hitl=False,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


# -----------------------------------------------------------------------------
# Reliability Scoring — composite SLI per service.
# -----------------------------------------------------------------------------


class ReliabilityScoreAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="reliability-score-agent",
        display_name="Reliability Scoring",
        workstream="sre",
        description="Composite reliability score: availability × latency × incident-rate.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-observability.query_metrics"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        service = state["input"].get("service", "checkout")
        state["_planned_calls"] = [
            ToolCall(tool="mcp-observability.query_metrics",
                     args={"metric": "availability_ratio", "service": service, "window_minutes": 60}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        service = state["input"].get("service", "checkout")
        res = next((r for r in state.get("tool_results") or [] if r.ok and "query_metrics" in r.tool), None)
        points = res.data.get("points", []) if res and res.data else []
        avail = sum(p["v"] for p in points) / max(1, len(points)) if points else 1.0
        score = round(avail * 0.6 + 0.3 * 0.95 + 0.1 * 0.9, 3)  # avail + latency + incident
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Reliability score for {service}: {score:.3f}.",
            action="publish_score",
            tool_calls=[],
            confidence=0.8,
            evidence=[EvidenceItem(source="composite", kind="metric",
                                   payload={"availability": avail, "score": score})],
            requires_hitl=False,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


# -----------------------------------------------------------------------------
# Runbook Authoring — ingests PIRs, transcripts, proposes new runbooks.
# -----------------------------------------------------------------------------


class RunbookAuthoringAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="runbook-authoring-agent",
        display_name="Runbook Authoring",
        workstream="sre",
        description="Ingest PIRs + chat; propose / update runbooks.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-runbook.propose_runbook", "mcp-knowledge.search_confluence"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        pir = state["input"].get("pir", {})
        title = pir.get("title", "Runbook")
        service = pir.get("service", "checkout")
        steps = [
            {"n": 1, "do": "Identify scope (service + severity)"},
            {"n": 2, "do": "Pull last 3 changes"},
            {"n": 3, "do": "Rollback if change < 30 min old"},
            {"n": 4, "do": "Escalate if error_rate > 5% after 10 min"},
        ]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Draft runbook proposed for {service}.",
            action="propose_runbook",
            tool_calls=[ToolCall(
                tool="mcp-runbook.propose_runbook",
                args={"title": f"{title} — mitigation", "service": service, "steps": steps, "tags": ["auto-drafted"]},
            )],
            confidence=0.8,
            evidence=[EvidenceItem(source="pir", kind="change", payload={"title": title})],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


# -----------------------------------------------------------------------------
# Observability Coverage — flags services with missing metrics / logs / traces.
# -----------------------------------------------------------------------------


class ObservabilityCoverageAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="obs-coverage-agent",
        display_name="Observability Coverage",
        workstream="sre",
        description="Flag services without metrics, logs, or traces.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.query_metrics", "mcp-observability.fetch_logs"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        services = await kg.all_services()
        gaps = [{"service": s.get("name"), "missing": ["rum"]} for s in services[:3]]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(gaps)} services missing observability signals.",
            action="propose_instrumentation",
            tool_calls=[],
            confidence=0.74,
            evidence=[EvidenceItem(source="coverage", kind="metric", payload={"gaps": gaps})],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
