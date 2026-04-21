"""CAB Automation Agent — builds the change advisory board packet.

Compiles risk, historical base rate, freeze conflicts, and sign-off
matrix; auto-approves low-risk changes and routes the rest.
"""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.kg.neo4j_client import kg
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class CABAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="cab-agent",
        display_name="CAB Automation",
        workstream="release",
        description="Compile CAB packet, auto-approve low-risk, route the rest.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-cicd.list_releases", "mcp-itsm.create_incident"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        change = state["input"].get("change", {})
        state["context"] = await kg.service_context(change.get("service", ""))
        state["_planned_calls"] = [
            ToolCall(
                tool="mcp-cicd.list_releases",
                args={"service": change.get("service"), "limit": 10},
            )
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        change = state["input"].get("change", {})
        results = state.get("tool_results", []) or []
        history = next((r.data for r in results if r.ok and "list_releases" in r.tool), [])
        risk = float(change.get("risk_score", 0.3))
        freeze = bool(change.get("in_freeze_window"))
        auto = risk < 0.3 and not freeze

        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=(
                f"CAB packet built — risk {risk:.2f}, freeze={freeze}. "
                + ("Auto-approved." if auto else "Routed to CAB reviewers.")
            ),
            action="auto_approve" if auto else "route_cab",
            tool_calls=[],
            confidence=0.86,
            evidence=[
                EvidenceItem(
                    source="cab",
                    kind="change",
                    payload={
                        "risk": risk,
                        "freeze": freeze,
                        "history_count": len(history),
                        "service": change.get("service"),
                    },
                )
            ],
            requires_hitl=not auto,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
