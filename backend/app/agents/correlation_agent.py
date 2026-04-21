"""Alert Correlation Agent — groups related alerts into a single incident."""
from __future__ import annotations

from collections import defaultdict
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


class CorrelationAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="correlation-agent",
        display_name="Alert Correlation",
        workstream="incident",
        description="Group related alerts by time, topology, and signal similarity.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-observability.list_alerts"],
        blast_radius={"max_services": 5},
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(
                tool="mcp-observability.list_alerts",
                args={},
                reason="Pull all active alerts",
            )
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        results = state.get("tool_results", []) or []
        alerts_result = next((r for r in results if r.ok and "list_alerts" in r.tool), None)
        alerts = alerts_result.data if alerts_result and alerts_result.data else []

        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for a in alerts:
            # Group by service + a topology-aware key derived from KG.
            svc = a.get("service", "unknown")
            ctx = await kg.service_context(svc)
            upstream_names = [u.get("name") for u in ctx.get("upstream", []) if u]
            key = svc if not upstream_names else upstream_names[0]
            groups[key].append(a)

        grouped = [
            {"cluster_key": k, "alert_count": len(v), "alerts": v}
            for k, v in groups.items()
        ]
        noise_reduction = 0.0
        if alerts:
            noise_reduction = 1.0 - (len(groups) / len(alerts))

        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=(
                f"Correlated {len(alerts)} alerts into {len(groups)} clusters "
                f"(noise reduction {noise_reduction:.0%})."
            ),
            action="create_incident_clusters",
            tool_calls=[],
            confidence=0.8,
            evidence=[
                EvidenceItem(
                    source="correlation",
                    kind="metric",
                    payload={"groups": grouped, "noise_reduction": noise_reduction},
                )
            ],
            requires_hitl=False,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
