"""Release Notes Agent — generates human-readable notes from commits/PRs."""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class ReleaseNotesAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="release-notes-agent",
        display_name="Release Notes",
        workstream="release",
        description="Draft release notes from commits + PRs + linked tickets.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-cicd.list_releases", "mcp-knowledge.upsert_article"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-cicd.list_releases", args={"service": state["input"].get("service"), "limit": 1}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        service = state["input"].get("service", "checkout")
        release = state["input"].get("release", {"id": "rel-next", "artifact": f"{service}:next"})
        notes = (
            f"# {release.get('id')} — {service}\n\n"
            "## Highlights\n"
            "- Performance: p95 latency down 8%\n"
            "- Reliability: retry policy fixed on upstream timeouts\n\n"
            "## Contents\n"
            "- PR #1421 `fix(orders): pool exhaustion under load`\n"
            "- PR #1423 `feat(checkout): idempotency-key support`\n"
            "- PR #1424 `chore(deps): bump jwt lib`\n"
        )
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Release notes drafted for {release.get('id')}.",
            action="publish_release_notes",
            tool_calls=[
                ToolCall(
                    tool="mcp-knowledge.upsert_article",
                    args={"title": f"Release notes — {release.get('id')}", "body": notes, "tags": ["release"]},
                )
            ],
            confidence=0.84,
            evidence=[EvidenceItem(source="ci", kind="change", payload={"release": release})],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
