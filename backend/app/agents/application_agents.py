"""Application agents — APM, LogAnalysis, DistributedTrace, RUM, Synthetic,
FeaturePerformance, SessionReplay.
"""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class APMAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="apm-agent",
        display_name="APM",
        workstream="stack",
        description="App latency, error rate, resource footprint.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.query_metrics"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        service = state["input"].get("service", "checkout")
        state["_planned_calls"] = [
            ToolCall(tool="mcp-observability.query_metrics",
                     args={"metric": "latency_p95", "service": service, "window_minutes": 30}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "query_metrics" in r.tool), None)
        latest = (res.data.get("latest") if res and res.data else 0.3) or 0.3
        regression = latest > 0.7
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"p95 latency {latest:.3f}.",
            action="investigate_regression" if regression else "monitor",
            tool_calls=[],
            confidence=0.75,
            evidence=[EvidenceItem(source="apm", kind="metric", payload={"p95": latest})],
            requires_hitl=regression,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class LogAnalysisAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="log-analysis-agent",
        display_name="Log Analysis",
        workstream="stack",
        description="Cluster log lines; surface anomaly templates.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.fetch_logs"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        service = state["input"].get("service", "checkout")
        state["_planned_calls"] = [
            ToolCall(tool="mcp-observability.fetch_logs",
                     args={"service": service, "query": "ERROR", "limit": 50}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "fetch_logs" in r.tool), None)
        logs = res.data if res and res.data else []
        errors = [l for l in logs if l.get("level") == "ERROR"]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(errors)} error lines in last window.",
            action="surface_anomaly" if len(errors) > 5 else "noop",
            tool_calls=[],
            confidence=0.7,
            evidence=[EvidenceItem(source="logs", kind="log", payload={"sample": errors[:5]})],
            requires_hitl=len(errors) > 5,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class DistributedTraceAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="trace-agent",
        display_name="Distributed Trace",
        workstream="stack",
        description="Span-level diagnosis + top-N slow edges.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.get_traces"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        service = state["input"].get("service", "checkout")
        state["_planned_calls"] = [
            ToolCall(tool="mcp-observability.get_traces", args={"service": service, "limit": 20})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "get_traces" in r.tool), None)
        traces = res.data if res and res.data else []
        slow = sorted(traces, key=lambda t: t.get("duration_ms", 0), reverse=True)[:3]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Slowest trace {slow[0]['duration_ms']}ms." if slow else "No traces.",
            action="surface_slow_edges",
            tool_calls=[],
            confidence=0.75,
            evidence=[EvidenceItem(source="traces", kind="trace", payload={"top": slow})],
            requires_hitl=False,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class RUMAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="rum-agent",
        display_name="Real-User Monitoring",
        workstream="stack",
        description="Frontend perf + error rate from real users.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.query_metrics"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-observability.query_metrics",
                     args={"metric": "rum_lcp_p75", "service": "web", "window_minutes": 30})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "query_metrics" in r.tool), None)
        latest = (res.data.get("latest") if res and res.data else 0.4) or 0.4
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"LCP p75 {latest:.2f}s.",
            action="propose_lcp_fix" if latest > 2.5 else "noop",
            tool_calls=[],
            confidence=0.68,
            evidence=[EvidenceItem(source="rum", kind="metric", payload={"lcp_p75": latest})],
            requires_hitl=latest > 2.5,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class SyntheticAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="synthetic-agent",
        display_name="Synthetic",
        workstream="stack",
        description="Track synthetic probe success + journey timings.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.query_metrics"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        probes = [
            {"journey": "checkout-smoketest", "success_pct": 0.98, "median_ms": 1420},
            {"journey": "login-smoketest", "success_pct": 1.0, "median_ms": 780},
        ]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Synthetic success across {len(probes)} journeys: all green.",
            action="noop",
            tool_calls=[],
            confidence=0.7,
            evidence=[EvidenceItem(source="synthetic", kind="metric", payload={"probes": probes})],
            requires_hitl=False,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class FeaturePerformanceAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="feature-perf-agent",
        display_name="Feature Performance",
        workstream="stack",
        description="Correlate feature flags with performance regressions.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-flags.list_flags", "mcp-observability.query_metrics"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [ToolCall(tool="mcp-flags.list_flags", args={})]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        flags = next((r.data for r in state.get("tool_results") or [] if r.ok and "list_flags" in r.tool), [])
        suspect = [f for f in flags if f.get("enabled")]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(suspect)} enabled flags considered for regression correlation.",
            action="propose_flag_experiment",
            tool_calls=[],
            confidence=0.66,
            evidence=[EvidenceItem(source="flags", kind="change", payload={"suspect": suspect})],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class SessionReplayAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="session-replay-agent",
        display_name="Session Replay",
        workstream="stack",
        description="Surface top failing sessions, propose repro.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=[],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        sessions = [
            {"id": "sess-1921", "errors": 3, "journey": "checkout"},
            {"id": "sess-2284", "errors": 2, "journey": "login"},
        ]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(sessions)} failing session clusters found.",
            action="surface_repro",
            tool_calls=[],
            confidence=0.65,
            evidence=[EvidenceItem(source="rum", kind="log", payload={"sessions": sessions})],
            requires_hitl=False,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
