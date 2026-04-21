"""Change Risk Scoring Agent — Phase 2, quantifies risk per change."""
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


class ChangeRiskAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="change-risk-agent",
        display_name="Change Risk Scoring",
        workstream="release",
        description="Score a proposed change on blast radius, history, freeze windows.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-cicd.list_releases"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        change = state["input"].get("change", {})
        service = change.get("service")
        state["_planned_calls"] = [
            ToolCall(
                tool="mcp-cicd.list_releases",
                args={"service": service, "limit": 10},
                reason="History of recent releases for base rate",
            )
        ]
        state["context"] = await kg.service_context(service) if service else {}
        return state

    async def decide(self, state: AgentState) -> AgentState:
        change = state["input"].get("change", {})
        context = state.get("context", {})
        results = state.get("tool_results", []) or []
        history = next(
            (r.data for r in results if r.ok and "list_releases" in r.tool), []
        )

        risk = 0.0
        factors: list[str] = []

        # Scope of dependents
        dependents = len(context.get("upstream", []) or [])
        if dependents >= 2:
            risk += 0.25
            factors.append(f"high_blast_radius ({dependents} upstream)")

        # Recent release velocity — more releases without incidents reduces risk
        if len(history) >= 5:
            risk += 0.05
        else:
            risk += 0.1
            factors.append("low_recent_release_velocity")

        # Tier weighting
        tier = (context.get("service") or {}).get("tier")
        if tier == "1":
            risk += 0.3
            factors.append("tier_1_service")

        # Type weighting
        t = change.get("change_type", "deploy")
        if t in ("infra", "db"):
            risk += 0.2
            factors.append(f"change_type_{t}")

        # Freeze window (mock: 20% of the time)
        if change.get("in_freeze_window"):
            risk += 0.2
            factors.append("freeze_window")

        risk = min(1.0, round(risk, 2))
        auto_approve = risk < 0.3 and t == "deploy"

        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=(
                f"Risk score {risk:.2f}. "
                + ("Auto-approval recommended." if auto_approve else "CAB review required.")
            ),
            action="auto_approve" if auto_approve else "cab_review",
            tool_calls=[],
            confidence=0.82,
            evidence=[
                EvidenceItem(
                    source="risk-model",
                    kind="metric",
                    payload={"risk_score": risk, "factors": factors},
                )
            ],
            requires_hitl=not auto_approve,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
