"""Remediation Agent — proposes (and at L2+, executes) containment actions.

Starts at L0 across the board. Earns autonomy per-service based on
eval scores + operator trust.
"""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class RemediationAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="remediation-agent",
        display_name="Remediation",
        workstream="incident",
        description="Propose containment: rollback, scale, silence, restart.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=[
            "mcp-cicd.rollback_deploy",
            "mcp-k8s.scale_deployment",
            "mcp-observability.silence_alert",
        ],
        blast_radius={"max_services": 1, "production": True},
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        cause = state["input"].get("top_cause", "recent_release")
        service = state["input"].get("service", "checkout")

        if cause == "recent_release":
            calls = [
                ToolCall(
                    tool="mcp-cicd.rollback_deploy",
                    args={"service": service, "to_revision": "previous"},
                    reason="Last-change correlation",
                )
            ]
            summary = f"Rollback {service} to previous known-good revision."
        elif cause == "capacity":
            calls = [
                ToolCall(
                    tool="mcp-k8s.scale_deployment",
                    args={"namespace": "prod", "name": service, "replicas": 8},
                    reason="Relieve capacity pressure",
                )
            ]
            summary = f"Scale {service} from current to 8 replicas."
        else:
            calls = []
            summary = "No high-confidence remediation; escalating to human."

        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=summary,
            action="apply_remediation",
            tool_calls=calls,
            confidence=0.65 if calls else 0.25,
            evidence=[EvidenceItem(source="input", kind="change", payload=state["input"])],
            requires_hitl=True,  # always HITL until L2 earned
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
