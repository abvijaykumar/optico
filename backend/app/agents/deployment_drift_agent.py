"""Deployment Drift Agent — detects live-vs-declared divergence."""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class DeploymentDriftAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="deployment-drift-agent",
        display_name="Deployment Drift",
        workstream="release",
        description="Detect GitOps / IaC drift; propose reconciliation.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-gitops.diff_state", "mcp-gitops.sync_app", "mcp-iac.detect_drift"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        app = state["input"].get("app", "checkout")
        state["_planned_calls"] = [
            ToolCall(tool="mcp-gitops.diff_state", args={"app": app}),
            ToolCall(tool="mcp-iac.detect_drift", args={"stack": app}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        app = state["input"].get("app", "checkout")
        results = state.get("tool_results") or []
        gitops = next((r.data for r in results if r.ok and "diff_state" in r.tool), {})
        iac = next((r.data for r in results if r.ok and "detect_drift" in r.tool), {})
        drifted = (not gitops.get("in_sync", True)) or iac.get("drifted", False)

        calls = []
        if drifted and gitops and not gitops.get("in_sync", True):
            calls.append(ToolCall(tool="mcp-gitops.sync_app", args={"app": app}))

        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=(
                f"Drift detected on {app}." if drifted else f"No drift on {app}."
            ),
            action="reconcile" if drifted else "noop",
            tool_calls=calls,
            confidence=0.82,
            evidence=[
                EvidenceItem(source="gitops", kind="change", payload=gitops),
                EvidenceItem(source="iac", kind="change", payload=iac),
            ],
            requires_hitl=drifted,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
