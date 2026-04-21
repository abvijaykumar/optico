"""Phase 4 agents — MajorIncidentPredictor, FinOps, Compliance,
SecurityCorrelation, KGMaintenance, Documentation.
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


# -----------------------------------------------------------------------------
# Major Incident Predictor — probabilistic major-incident forecast.
# -----------------------------------------------------------------------------


class MajorIncidentPredictorAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="major-incident-predictor",
        display_name="Major Incident Predictor",
        workstream="analytics",
        description="Predict probability of major incident in the next N hours.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.query_metrics", "mcp-cicd.list_releases"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        service = state["input"].get("service", "checkout")
        state["_planned_calls"] = [
            ToolCall(tool="mcp-observability.query_metrics",
                     args={"metric": "error_rate", "service": service, "window_minutes": 60}),
            ToolCall(tool="mcp-cicd.list_releases", args={"service": service, "limit": 5}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        service = state["input"].get("service", "checkout")
        results = state.get("tool_results") or []
        err = next((r for r in results if r.ok and "query_metrics" in r.tool), None)
        rels = next((r.data for r in results if r.ok and "list_releases" in r.tool), [])
        latest_err = (err.data.get("latest") if err and err.data else 0.02) or 0.02

        # Simple log-odds model — production version uses gradient-boosted model.
        score = 0.0
        if latest_err > 0.05:
            score += 0.35
        if any(r.get("status") == "canary" for r in rels):
            score += 0.25
        if any(r.get("status") == "rolled_back" for r in rels):
            score += 0.4
        prob = min(0.95, score)

        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Major-incident probability on {service} (4h): {prob:.0%}.",
            action="preemptive_alert" if prob > 0.5 else "monitor",
            tool_calls=[],
            confidence=0.7,
            evidence=[EvidenceItem(source="predictor", kind="metric",
                                   payload={"prob_4h": prob, "err_rate": latest_err})],
            requires_hitl=prob > 0.5,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


# -----------------------------------------------------------------------------
# FinOps Agent
# -----------------------------------------------------------------------------


class FinOpsAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="finops-agent",
        display_name="FinOps",
        workstream="analytics",
        description="Spend anomalies, budgets, unit economics.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-finops.spend_query", "mcp-finops.budget_alert",
               "mcp-finops.rightsizing_recommend"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-finops.budget_alert", args={}),
            ToolCall(tool="mcp-finops.rightsizing_recommend", args={}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        budgets = next((r.data for r in state.get("tool_results") or [] if r.ok and "budget_alert" in r.tool), [])
        saving = sum(r.get("saving_usd", 0)
                     for r in (next((t.data for t in state.get("tool_results") or [] if t.ok and "rightsizing" in t.tool), [])))
        alerts = [b for b in budgets if b.get("pct", 0) > 0.9]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(alerts)} budget alerts, ~${saving}/mo rightsizing potential.",
            action="publish_finops_report",
            tool_calls=[],
            confidence=0.78,
            evidence=[
                EvidenceItem(source="budgets", kind="metric", payload={"alerts": alerts}),
                EvidenceItem(source="rightsizing", kind="metric", payload={"saving_usd": saving}),
            ],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


# -----------------------------------------------------------------------------
# Compliance / Audit Agent
# -----------------------------------------------------------------------------


class ComplianceAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="compliance-agent",
        display_name="Compliance & Audit",
        workstream="analytics",
        description="Continuously gather audit evidence; detect policy drift.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-security.policy_check", "mcp-security.vault_read"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-security.policy_check", args={"resource": "s3://audit-logs"}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "policy_check" in r.tool), None)
        data = res.data if res and res.data else {}
        findings = data.get("violations", [])
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Compliance: {len(findings)} violation(s) found.",
            action="open_finding" if findings else "noop",
            tool_calls=[],
            confidence=0.86,
            evidence=[EvidenceItem(source="opa", kind="change", payload=data)],
            requires_hitl=bool(findings),
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


# -----------------------------------------------------------------------------
# Security Correlation Agent
# -----------------------------------------------------------------------------


class SecurityCorrelationAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="sec-correlation-agent",
        display_name="Security Correlation",
        workstream="analytics",
        description="Correlate SIEM events + IOCs + change context into incidents.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-security.siem_query", "mcp-security.ioc_lookup"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-security.siem_query", args={"query": "failed_login OR policy_violation"}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "siem_query" in r.tool), None)
        events = res.data if res and res.data else []
        severe = [e for e in events if e.get("event") == "policy_violation"]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(severe)} high-severity security correlations.",
            action="open_security_incident" if severe else "monitor",
            tool_calls=[],
            confidence=0.78,
            evidence=[EvidenceItem(source="siem", kind="log", payload={"events": events})],
            requires_hitl=bool(severe),
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


# -----------------------------------------------------------------------------
# KG Maintenance Agent — stewards the knowledge graph
# -----------------------------------------------------------------------------


class KGMaintenanceAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="kg-maintenance-agent",
        display_name="KG Maintenance",
        workstream="analytics",
        description="Detect stale nodes, merge duplicates, audit schema conformance.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=[],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        services = await kg.all_services()
        duplicates = []  # in-memory graph has no duplicates; real Neo4j version does similarity search
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"KG health: {len(services)} service nodes, {len(duplicates)} duplicate candidates.",
            action="publish_kg_health",
            tool_calls=[],
            confidence=0.8,
            evidence=[EvidenceItem(source="kg-audit", kind="metric",
                                   payload={"services": len(services), "dupes": duplicates})],
            requires_hitl=False,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


# -----------------------------------------------------------------------------
# Documentation Agent — keeps docs in sync with code + KG
# -----------------------------------------------------------------------------


class DocumentationAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="documentation-agent",
        display_name="Documentation",
        workstream="analytics",
        description="Detect stale docs; propose updates grounded in KG + code.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-knowledge.search_confluence", "mcp-knowledge.upsert_article"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-knowledge.search_confluence", args={"query": "architecture"})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "search_confluence" in r.tool), None)
        articles = res.data if res and res.data else []
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Reviewed {len(articles)} articles; proposed refresh for 2.",
            action="propose_doc_refresh",
            tool_calls=[],
            confidence=0.7,
            evidence=[EvidenceItem(source="kb", kind="change", payload={"count": len(articles)})],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
