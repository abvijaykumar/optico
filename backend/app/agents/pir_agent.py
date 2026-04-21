"""PIR (Post-Incident Review) Agent — drafts the write-up."""
from __future__ import annotations

from datetime import datetime, timezone

from app.agents.base import AgentBase, AgentState
from app.agents.llm import get_llm
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


_PIR_TEMPLATE = """# Post-Incident Review — {title}

## Summary
{summary}

## Timeline (UTC)
{timeline}

## Impact
- Services: {services}
- MTTR: {mttr}
- Severity: {severity}

## Contributing factors
{factors}

## 5 Whys
1. Why did the outage occur? — {why1}
2. Why did {why1_short}? — {why2}
3. Why did {why2_short}? — {why3}
4. Why did {why3_short}? — {why4}
5. Why did {why4_short}? — {why5}

## Action items
{actions}

## KEDB candidate
{kedb}
"""


class PIRAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="pir-agent",
        display_name="Post-Incident Review",
        workstream="incident",
        description="Draft PIR from KG timeline + RCA output for human sign-off.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-knowledge.upsert_article", "mcp-itsm.search_kedb"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        incident = state["input"].get("incident", {})
        rca = state["input"].get("rca", {})
        title = incident.get("title", "Incident")
        severity = incident.get("severity", "SEV2")
        services = ", ".join(incident.get("services", []))
        timeline = "\n".join(
            f"- {evt.get('ts','?')}: {evt.get('event','?')}"
            for evt in incident.get("timeline", [])
        ) or "- (timeline pending)"
        factors = rca.get("top_cause", "Pending RCA")
        mttr = incident.get("mttr_seconds")
        mttr_str = f"{round(mttr/60, 1)} min" if mttr else "—"

        body = _PIR_TEMPLATE.format(
            title=title,
            summary=rca.get("summary", "Summary pending."),
            timeline=timeline,
            services=services or "—",
            mttr=mttr_str,
            severity=severity,
            factors=factors,
            why1="Service returned 5xx after deploy",
            why1_short="5xx after deploy",
            why2="Missing env var in canary pod",
            why2_short="missing env var",
            why3="Manifest diff not enforced",
            why3_short="manifest drift",
            why4="No pre-deploy verification gate",
            why4_short="no gate",
            why5="Gate policy not written as code",
            actions=(
                "- Add OPA gate for env var parity (owner: platform)\n"
                "- Backfill canary verification test (owner: release-eng)\n"
                "- Add KEDB entry and link from runbook (owner: SRE)"
            ),
            kedb="KEDB-102: Checkout 500s after deploy — env var drift",
        )

        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"PIR draft ready for {title} ({severity}).",
            action="publish_pir_draft",
            tool_calls=[
                ToolCall(
                    tool="mcp-knowledge.upsert_article",
                    args={
                        "title": f"PIR — {title}",
                        "body": body,
                        "tags": ["pir", severity.lower()],
                    },
                )
            ],
            confidence=0.88,
            evidence=[
                EvidenceItem(source="pir-template", kind="change", payload={"length": len(body)}),
            ],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        state["pir_body"] = body
        return state
