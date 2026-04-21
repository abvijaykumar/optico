"""RCA Agent — hypothesis tree over logs, metrics, traces, changes."""
from __future__ import annotations

from typing import Any

from app.agents.base import AgentBase, AgentState
from app.agents.llm import get_llm
from app.kg.neo4j_client import kg
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class RCAAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="rca-agent",
        display_name="Root Cause Analysis",
        workstream="incident",
        description="Enumerate hypotheses, gather evidence, rank causes.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=[
            "mcp-observability.fetch_logs",
            "mcp-observability.get_traces",
            "mcp-observability.query_metrics",
            "mcp-cicd.list_releases",
        ],
    )

    async def plan(self, state: AgentState) -> AgentState:
        incident = state["input"].get("incident", {})
        service = incident.get("service") or (incident.get("services") or ["checkout"])[0]
        state["context"] = await kg.service_context(service)
        recent_changes = await kg.recent_changes_for(service, limit=5)
        state["context"]["recent_changes"] = recent_changes

        state["_planned_calls"] = [
            ToolCall(
                tool="mcp-observability.fetch_logs",
                args={"service": service, "query": "ERROR", "limit": 50},
                reason="Error-level log pull for clues",
            ),
            ToolCall(
                tool="mcp-observability.get_traces",
                args={"service": service, "limit": 10},
                reason="Trace-level latency / failure distribution",
            ),
            ToolCall(
                tool="mcp-observability.query_metrics",
                args={"metric": "error_rate", "service": service, "window_minutes": 60},
            ),
            ToolCall(
                tool="mcp-cicd.list_releases",
                args={"service": service, "limit": 5},
                reason="Did a recent change land?",
            ),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        results = state.get("tool_results", []) or []
        context = state.get("context", {})
        incident = state["input"].get("incident", {})

        recent_releases = next(
            (r.data for r in results if r.ok and "list_releases" in r.tool), []
        )
        logs = next((r.data for r in results if r.ok and "fetch_logs" in r.tool), [])
        traces = next((r.data for r in results if r.ok and "get_traces" in r.tool), [])
        err_points = next(
            (r.data for r in results if r.ok and "query_metrics" in r.tool), {}
        )

        # Build a ranked hypothesis list deterministically, then ask the LLM
        # to narrate — explainability first.
        hypotheses: list[dict[str, Any]] = []
        if recent_releases:
            hypotheses.append(
                {
                    "cause": f"Recent release {recent_releases[0]['id']} on "
                    f"{recent_releases[0]['service']}",
                    "confidence": 0.78,
                    "evidence": recent_releases[0],
                }
            )
        if traces and any(t.get("error") for t in traces):
            hypotheses.append(
                {
                    "cause": "Upstream trace errors (>= 1 failing span)",
                    "confidence": 0.42,
                    "evidence": [t for t in traces if t.get("error")][:3],
                }
            )
        if logs and any(l.get("level") == "ERROR" for l in logs):
            hypotheses.append(
                {
                    "cause": "Error-log volume burst",
                    "confidence": 0.35,
                    "evidence": [l for l in logs if l["level"] == "ERROR"][:3],
                }
            )
        if not hypotheses:
            hypotheses.append(
                {"cause": "Insufficient signal — escalate", "confidence": 0.2, "evidence": {}}
            )

        top = max(hypotheses, key=lambda h: h["confidence"])
        prompt = (
            "You are an SRE writing the opening line of an RCA. "
            "In one sentence, state the most likely root cause given this evidence:\n"
            f"Top hypothesis: {top['cause']}\n"
            f"Recent releases: {recent_releases[:2]}\n"
            f"Error metric points (tail): {err_points.get('points', [])[-3:] if err_points else []}\n"
        )
        try:
            summary = get_llm().invoke(prompt).content  # type: ignore[union-attr]
        except Exception:
            summary = top["cause"]

        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=str(summary),
            action="propose_remediation",
            tool_calls=[],
            confidence=float(top["confidence"]),
            evidence=[
                EvidenceItem(
                    source="hypothesis-tree",
                    kind="metric",
                    payload={"hypotheses": hypotheses, "kg_context": context},
                )
            ],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
