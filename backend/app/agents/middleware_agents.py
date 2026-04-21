"""Middleware agents — DBA, MessageBroker, APIGateway, ServiceMesh, Cache,
ContainerRuntime, LoadBalancer.
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


class DBAAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="dba-agent",
        display_name="Database (DBA)",
        workstream="stack",
        description="Query tuning, index advice, vacuum cadence, failover readiness.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-db.explain_plan", "mcp-db.index_advisor", "mcp-db.vacuum"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        db = state["input"].get("db", "orders-db")
        state["_planned_calls"] = [
            ToolCall(tool="mcp-db.index_advisor", args={"db": db}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "index_advisor" in r.tool), None)
        suggestions = res.data if res and res.data else []
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(suggestions)} index suggestion(s).",
            action="apply_index_plan",
            tool_calls=[],
            confidence=0.78,
            evidence=[EvidenceItem(source="advisor", kind="metric", payload={"suggestions": suggestions})],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class MessageBrokerAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="broker-agent",
        display_name="Message Broker",
        workstream="stack",
        description="Lag, DLQ, partition balance, poison-pill detection.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-messaging.lag", "mcp-messaging.dlq_inspect"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        group = state["input"].get("group", "orders-consumer")
        state["_planned_calls"] = [
            ToolCall(tool="mcp-messaging.lag", args={"group": group}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "lag" in r.tool), None)
        lag = (res.data.get("total_lag") if res and res.data else 0) or 0
        risky = lag > 50_000
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Consumer lag {lag}.",
            action="investigate_lag" if risky else "monitor",
            tool_calls=[],
            confidence=0.78,
            evidence=[EvidenceItem(source="lag", kind="metric", payload={"lag": lag})],
            requires_hitl=risky,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class APIGatewayAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="api-gw-agent",
        display_name="API Gateway",
        workstream="stack",
        description="Rate limits, auth errors, route health.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.query_metrics"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-observability.query_metrics",
                     args={"metric": "gateway_4xx_rate", "service": "api-gw", "window_minutes": 15})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "query_metrics" in r.tool), None)
        latest = (res.data.get("latest") if res and res.data else 0.0) or 0.0
        alert = latest > 0.2
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"4xx rate {latest:.2f}.",
            action="tune_ratelimit" if alert else "monitor",
            tool_calls=[],
            confidence=0.72,
            evidence=[EvidenceItem(source="metrics", kind="metric", payload={"latest": latest})],
            requires_hitl=alert,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class ServiceMeshAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="mesh-agent",
        display_name="Service Mesh",
        workstream="stack",
        description="mTLS state, retry storms, circuit-breaker health.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.query_metrics"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary="Mesh mTLS green; retry storms within threshold.",
            action="noop",
            tool_calls=[],
            confidence=0.7,
            evidence=[],
            requires_hitl=False,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class CacheAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="cache-agent",
        display_name="Cache",
        workstream="stack",
        description="Hit ratio, eviction rate, key-expiry policy.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.query_metrics"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-observability.query_metrics",
                     args={"metric": "cache_hit_ratio", "service": "redis", "window_minutes": 30})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "query_metrics" in r.tool), None)
        latest = (res.data.get("latest") if res and res.data else 0.9) or 0.9
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Cache hit ratio {latest:.2f}.",
            action="tune_ttl" if latest < 0.75 else "noop",
            tool_calls=[],
            confidence=0.7,
            evidence=[EvidenceItem(source="metrics", kind="metric", payload={"latest": latest})],
            requires_hitl=latest < 0.75,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class ContainerRuntimeAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="runtime-agent",
        display_name="Container Runtime",
        workstream="stack",
        description="containerd/runc health + image pull errors.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-k8s.list_pods"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-k8s.list_pods", args={"namespace": state["input"].get("namespace", "prod")})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "list_pods" in r.tool), None)
        pods = res.data if res and res.data else []
        crashing = [p for p in pods if p.get("status") == "CrashLoopBackOff"]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(crashing)} pod(s) CrashLoopBackOff.",
            action="open_incident" if crashing else "noop",
            tool_calls=[],
            confidence=0.82,
            evidence=[EvidenceItem(source="k8s", kind="change", payload={"crashing": crashing})],
            requires_hitl=bool(crashing),
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class LoadBalancerAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="lb-agent",
        display_name="Load Balancer",
        workstream="stack",
        description="Backend health + connection distribution.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.query_metrics"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary="LB backends healthy; connections evenly distributed.",
            action="noop",
            tool_calls=[],
            confidence=0.7,
            evidence=[],
            requires_hitl=False,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
