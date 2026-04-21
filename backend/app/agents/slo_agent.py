"""SLO / Error Budget Agent — tracks burn rate, flags breach risk."""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class SLOAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="slo-agent",
        display_name="SLO / Error Budget",
        workstream="sre",
        description="Compute SLI burn rate and flag error-budget risk.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-observability.query_metrics"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        service = state["input"].get("service", "checkout")
        state["_planned_calls"] = [
            ToolCall(
                tool="mcp-observability.query_metrics",
                args={"metric": "availability_ratio", "service": service, "window_minutes": 60},
            )
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        results = state.get("tool_results", []) or []
        res = next((r for r in results if r.ok and "query_metrics" in r.tool), None)
        points = res.data.get("points", []) if res and res.data else []
        if not points:
            availability = 1.0
        else:
            availability = sum(p["v"] for p in points) / len(points)
        slo = 0.995
        burn = max(0.0, 1.0 - availability) / max(1e-6, 1.0 - slo)
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=(
                f"SLO burn rate {burn:.2f}x. "
                + ("Breach risk — page SRE." if burn > 10 else "Within budget.")
            ),
            action="page_oncall" if burn > 10 else "monitor",
            tool_calls=[],
            confidence=0.75,
            evidence=[
                EvidenceItem(
                    source="slo",
                    kind="metric",
                    payload={"availability": availability, "burn_rate": burn, "slo": slo},
                )
            ],
            requires_hitl=burn > 10,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
