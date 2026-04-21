"""Feature Flag Governance Agent — detects stale flags, unsafe combos, drift."""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class FeatureFlagGovernanceAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="feature-flag-agent",
        display_name="Feature Flag Governance",
        workstream="release",
        description="Flag staleness, ownership, risky toggles; recommend cleanups.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-flags.list_flags", "mcp-flags.toggle_flag"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [ToolCall(tool="mcp-flags.list_flags", args={})]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        flags = next(
            (r.data for r in state.get("tool_results") or [] if r.ok and "list_flags" in r.tool),
            [],
        )
        stale = [f for f in flags if f.get("stale_days", 0) > 90]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(stale)} stale flag(s) detected (> 90d unchanged).",
            action="propose_flag_cleanup",
            tool_calls=[],
            confidence=0.75,
            evidence=[
                EvidenceItem(source="flags", kind="change", payload={"stale": stale}),
            ],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
