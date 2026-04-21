"""Release Orchestration Agent — drives canary → promote → post-deploy verify."""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class ReleaseAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="release-agent",
        display_name="Release Orchestration",
        workstream="release",
        description="Drive canary rollout, health gate, promote or rollback.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=[
            "mcp-cicd.trigger_pipeline",
            "mcp-cicd.promote_artifact",
            "mcp-cicd.rollback_deploy",
            "mcp-observability.query_metrics",
        ],
    )

    async def plan(self, state: AgentState) -> AgentState:
        change = state["input"].get("change", {})
        service = change.get("service", "checkout")
        state["_planned_calls"] = [
            ToolCall(
                tool="mcp-observability.query_metrics",
                args={"metric": "error_rate", "service": service, "window_minutes": 5},
                reason="Post-deploy health gate",
            )
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        change = state["input"].get("change", {})
        service = change.get("service", "checkout")
        artifact = change.get("artifact") or f"{service}:next"
        results = state.get("tool_results", []) or []
        gate = next((r for r in results if r.ok and "query_metrics" in r.tool), None)
        latest = gate.data.get("latest") if gate and gate.data else 0.0
        healthy = latest is not None and latest < 0.05

        action = "promote" if healthy else "rollback"
        calls = [
            (
                ToolCall(
                    tool="mcp-cicd.promote_artifact",
                    args={"artifact": artifact, "target_env": "prod"},
                    reason="Canary healthy — promote",
                )
                if healthy
                else ToolCall(
                    tool="mcp-cicd.rollback_deploy",
                    args={"service": service},
                    reason="Canary unhealthy — rollback",
                )
            )
        ]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=(
                f"Canary {'healthy — promoting' if healthy else 'unhealthy — rolling back'} "
                f"{artifact} on {service}."
            ),
            action=action,
            tool_calls=calls,
            confidence=0.83 if healthy else 0.77,
            evidence=[
                EvidenceItem(
                    source="gate",
                    kind="metric",
                    payload={"error_rate": latest, "healthy": healthy},
                )
            ],
            requires_hitl=not healthy,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
