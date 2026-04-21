"""Canary Agent — drives progressive rollout with health gates."""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class CanaryAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="canary-agent",
        display_name="Canary Rollout",
        workstream="release",
        description="Progressive rollout: 5→25→50→100% gated on health.",
        autonomy_level=AutonomyLevel.L2_APPLY_WITH_REVIEW,
        tools=[
            "mcp-observability.query_metrics",
            "mcp-cicd.trigger_pipeline",
            "mcp-cicd.rollback_deploy",
        ],
    )

    async def plan(self, state: AgentState) -> AgentState:
        change = state["input"].get("change", {})
        service = change.get("service", "checkout")
        state["_planned_calls"] = [
            ToolCall(
                tool="mcp-observability.query_metrics",
                args={"metric": "error_rate", "service": service, "window_minutes": 5},
            )
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        change = state["input"].get("change", {})
        service = change.get("service", "checkout")
        stage = state["input"].get("stage", 5)  # % traffic
        res = next(
            (r for r in state.get("tool_results") or [] if r.ok and "query_metrics" in r.tool),
            None,
        )
        latest = (res.data.get("latest") if res and res.data else 0.0) or 0.0
        healthy = latest < 0.05
        next_stage = {5: 25, 25: 50, 50: 100}.get(stage, 100)

        calls = []
        action = "promote_canary"
        if healthy:
            calls.append(
                ToolCall(
                    tool="mcp-cicd.trigger_pipeline",
                    args={"pipeline": f"canary-{service}", "params": {"percentage": next_stage}},
                    reason=f"Canary healthy — advance {stage}→{next_stage}%",
                )
            )
        else:
            action = "abort_canary"
            calls.append(
                ToolCall(
                    tool="mcp-cicd.rollback_deploy",
                    args={"service": service},
                    reason="Canary unhealthy — abort",
                )
            )

        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=(
                f"Canary {service} at {stage}% — error_rate {latest:.3f}. "
                + (f"Advancing to {next_stage}%." if healthy else "Aborting.")
            ),
            action=action,
            tool_calls=calls,
            confidence=0.82 if healthy else 0.78,
            evidence=[
                EvidenceItem(source="gate", kind="metric",
                             payload={"stage": stage, "next": next_stage, "error_rate": latest}),
            ],
            requires_hitl=not healthy,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
