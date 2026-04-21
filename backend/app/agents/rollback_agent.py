"""Rollback Agent — decides and executes rollback with guardrails."""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class RollbackAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="rollback-agent",
        display_name="Rollback",
        workstream="release",
        description="Recommend / execute rollback to a prior known-good revision.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-cicd.list_releases", "mcp-cicd.rollback_deploy"],
        blast_radius={"production": True, "max_services": 1},
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(
                tool="mcp-cicd.list_releases",
                args={"service": state["input"].get("service"), "limit": 5},
            )
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        service = state["input"].get("service", "checkout")
        history = next(
            (r.data for r in state.get("tool_results") or [] if r.ok and "list_releases" in r.tool),
            [],
        )
        target = next(
            (r for r in history if r.get("status") == "deployed"),
            {"id": "previous"},
        )
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Rollback {service} to {target.get('id')}.",
            action="rollback",
            tool_calls=[
                ToolCall(
                    tool="mcp-cicd.rollback_deploy",
                    args={"service": service, "to_revision": target.get("id")},
                )
            ],
            confidence=0.88,
            evidence=[EvidenceItem(source="release-history", kind="change", payload=target)],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
