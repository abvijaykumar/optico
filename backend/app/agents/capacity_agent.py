"""Capacity Forecasting Agent — simple linear projection over metric series."""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class CapacityAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="capacity-agent",
        display_name="Capacity Forecast",
        workstream="sre",
        description="Forecast capacity headroom and flag breach risk by service.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.query_metrics"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        service = state["input"].get("service", "checkout")
        state["_planned_calls"] = [
            ToolCall(
                tool="mcp-observability.query_metrics",
                args={"metric": "cpu_utilisation", "service": service, "window_minutes": 60},
            )
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        results = state.get("tool_results", []) or []
        res = next((r for r in results if r.ok and "query_metrics" in r.tool), None)
        points = res.data.get("points", []) if res and res.data else []
        if len(points) < 2:
            avg = 0.5
            slope = 0.0
        else:
            xs = list(range(len(points)))
            ys = [p["v"] for p in points]
            avg = sum(ys) / len(ys)
            # least-squares slope
            n = len(xs)
            mx = sum(xs) / n
            my = avg
            num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            den = sum((x - mx) ** 2 for x in xs) or 1
            slope = num / den

        projected_7d = min(1.0, max(0.0, avg + slope * 60 * 24 * 7))
        breach = projected_7d > 0.85

        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=(
                f"CPU avg {avg:.2f}; 7-day projection {projected_7d:.2f}. "
                + ("Breach risk — recommend scale-out." if breach else "Headroom OK.")
            ),
            action="scale_out" if breach else "monitor",
            tool_calls=[],
            confidence=0.7,
            evidence=[
                EvidenceItem(
                    source="forecast",
                    kind="metric",
                    payload={"avg": avg, "slope": slope, "projection_7d": projected_7d},
                )
            ],
            requires_hitl=breach,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
