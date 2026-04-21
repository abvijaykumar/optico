"""Triage Agent — classifies incoming alerts, routes, suggests next action."""
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


class TriageAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="triage-agent",
        display_name="Alert Triage",
        workstream="incident",
        description="Classify alerts, enrich with context, route to the right runbook or on-call.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-observability.list_alerts", "mcp-observability.query_metrics",
               "mcp-itsm.search_kedb", "mcp-runbook.search_runbook"],
        blast_radius={"max_services": 1},
    )

    async def plan(self, state: AgentState) -> AgentState:
        alert = state["input"].get("alert", {})
        service = alert.get("service", "unknown")
        state["context"] = await kg.service_context(service)
        state["_planned_calls"] = [
            ToolCall(
                tool="mcp-observability.query_metrics",
                args={"metric": "error_rate", "service": service, "window_minutes": 15},
                reason="Confirm the signal is real",
            ),
            ToolCall(
                tool="mcp-itsm.search_kedb",
                args={"query": alert.get("signal", service)},
                reason="Check for known errors",
            ),
            ToolCall(
                tool="mcp-runbook.search_runbook",
                args={"service": service},
                reason="Fetch candidate runbooks",
            ),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        alert = state["input"].get("alert", {})
        results = state.get("tool_results", []) or []
        metric_result = next((r for r in results if "query_metrics" in r.tool and r.ok), None)
        kedb_result = next((r for r in results if "search_kedb" in r.tool and r.ok), None)
        runbook_result = next((r for r in results if "search_runbook" in r.tool and r.ok), None)

        latest = metric_result.data.get("latest") if metric_result and metric_result.data else None
        known = kedb_result.data if kedb_result and kedb_result.data else []
        runbooks = runbook_result.data if runbook_result and runbook_result.data else []

        severity = alert.get("severity", "SEV3")
        if latest is not None and latest > 0.5:
            severity = "SEV1"
        elif latest is not None and latest > 0.2:
            severity = "SEV2"

        evidence = [
            EvidenceItem(source="metrics", kind="metric", payload={"latest": latest}),
            EvidenceItem(source="kedb", kind="change", payload={"matches": known[:3]}),
            EvidenceItem(source="runbook", kind="change", payload={"candidates": runbooks[:3]}),
        ]

        suggested_runbook = runbooks[0] if runbooks else None
        summary = (
            f"Alert {alert.get('signal','?')} on {alert.get('service','?')} "
            f"classified as {severity}. "
            + (f"Known error match: {known[0]['id']}. " if known else "No KEDB match. ")
            + (f"Runbook: {suggested_runbook['id']}." if suggested_runbook else "No runbook matched.")
        )

        confidence = 0.85 if known else (0.7 if runbooks else 0.55)

        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=summary,
            action="open_incident" if severity in ("SEV1", "SEV2") else "notify_oncall",
            tool_calls=[
                ToolCall(
                    tool="mcp-itsm.create_incident",
                    args={
                        "title": alert.get("signal", "Triage alert"),
                        "severity": severity,
                        "service": alert.get("service", "unknown"),
                        "summary": summary,
                    },
                )
            ] if severity in ("SEV1", "SEV2") else [],
            confidence=confidence,
            evidence=evidence,
            requires_hitl=severity == "SEV1",
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
