"""KEDB Agent — extracts candidate known-error entries from PIRs."""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class KEDBAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="kedb-agent",
        display_name="KEDB Curation",
        workstream="incident",
        description="Extract candidate Known Error entries from PIRs; surface on matches.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-itsm.search_kedb", "mcp-knowledge.upsert_article"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        pir = state["input"].get("pir", {})
        title = pir.get("title", "Known error")
        symptoms = pir.get("symptoms", [])
        root_cause = pir.get("root_cause", "unknown")
        workaround = pir.get("workaround", "restart and rollback")
        body = (
            f"# KEDB — {title}\n\n## Symptoms\n" + "\n".join(f"- {s}" for s in symptoms)
            + f"\n\n## Root cause\n{root_cause}\n\n## Workaround\n{workaround}\n"
        )
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"KEDB candidate drafted from PIR “{title}”.",
            action="publish_kedb_candidate",
            tool_calls=[
                ToolCall(
                    tool="mcp-knowledge.upsert_article",
                    args={"title": f"KEDB — {title}", "body": body, "tags": ["kedb"]},
                )
            ],
            confidence=0.8,
            evidence=[
                EvidenceItem(
                    source="pir", kind="change", payload={"symptoms": symptoms}
                )
            ],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
