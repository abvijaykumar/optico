"""Base agent — all specialist agents inherit this contract.

Every agent:
  * declares an `AgentDescriptor` (workstream, tools, blast-radius)
  * executes through a LangGraph state machine
  * emits an `AgentRecommendation` with evidence, confidence, and audit
  * respects the autonomy policy + policy engine on every tool call
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TypedDict

from app.core.logging import get_logger
from app.eval.harness import eval_harness
from app.governance.autonomy import autonomy_registry
from app.governance.policy import policy_engine
from app.hitl.broker import hitl_broker
from app.mcp.base import ToolResult, tool_vault
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AgentRun,
    AutonomyLevel,
    HITLDecision,
    ToolCall,
)

log = get_logger(__name__)


class AgentState(TypedDict, total=False):
    """Shared LangGraph state. Subclasses may add keys via `Annotated`."""

    input: dict[str, Any]
    context: dict[str, Any]
    tool_results: list[ToolResult]
    scratchpad: list[str]
    recommendation: AgentRecommendation | None
    hitl_item_id: str | None
    decision: str | None
    error: str | None


@dataclass
class AgentContext:
    agent: str
    input: dict[str, Any]
    kg_context: dict[str, Any] = field(default_factory=dict)
    tool_results: list[ToolResult] = field(default_factory=list)


class AgentBase(ABC):
    descriptor: AgentDescriptor

    def __init__(self) -> None:
        if not hasattr(self, "descriptor"):
            raise NotImplementedError("Agent must define a class-level descriptor")
        policy = autonomy_registry.get(self.descriptor.name)
        policy.level = self.descriptor.autonomy_level
        self._graph = self._build_graph()

    # -- subclass hooks ----------------------------------------------------

    @abstractmethod
    async def plan(self, state: AgentState) -> AgentState:
        """Decide which tools to call and produce a scratchpad entry."""

    @abstractmethod
    async def decide(self, state: AgentState) -> AgentState:
        """Produce the final AgentRecommendation from tool results."""

    # -- LangGraph wiring --------------------------------------------------

    def _build_graph(self):
        # Imported locally so import cost is paid at first use.
        from langgraph.graph import END, StateGraph

        graph = StateGraph(dict)  # TypedDict accepted as dict at runtime
        graph.add_node("plan", self._wrap(self.plan))
        graph.add_node("call_tools", self._wrap(self._call_tools))
        graph.add_node("decide", self._wrap(self.decide))
        graph.add_node("hitl", self._wrap(self._maybe_hitl))
        graph.add_node("execute", self._wrap(self._execute_if_allowed))

        graph.set_entry_point("plan")
        graph.add_edge("plan", "call_tools")
        graph.add_edge("call_tools", "decide")
        graph.add_edge("decide", "hitl")
        graph.add_edge("hitl", "execute")
        graph.add_edge("execute", END)

        return graph.compile()

    @staticmethod
    def _wrap(coro):
        async def _run(state):
            return await coro(state) or state
        return _run

    # -- tool execution ----------------------------------------------------

    async def _call_tools(self, state: AgentState) -> AgentState:
        rec = state.get("recommendation")
        planned_calls: list[ToolCall] = state.get("_planned_calls", [])  # type: ignore[arg-type]
        results: list[ToolResult] = state.get("tool_results", []) or []

        for call in planned_calls:
            policy = autonomy_registry.get(self.descriptor.name)
            decision = policy_engine.evaluate(
                agent=self.descriptor.name,
                autonomy_level=policy.level,
                call=call,
                context={"blast_radius": self.descriptor.blast_radius},
            )
            if not decision.allowed:
                log.warning(
                    "agent.tool_denied",
                    agent=self.descriptor.name,
                    tool=call.tool,
                    reason=decision.reason,
                )
                results.append(
                    ToolResult(tool=call.tool, ok=False, error=decision.reason)
                )
                continue
            result = await tool_vault.call(call.tool, call.args)
            results.append(result)
            log.info(
                "agent.tool_called",
                agent=self.descriptor.name,
                tool=call.tool,
                ok=result.ok,
            )
        state["tool_results"] = results
        return state

    # -- HITL --------------------------------------------------------------

    async def _maybe_hitl(self, state: AgentState) -> AgentState:
        rec = state.get("recommendation")
        if rec is None:
            return state
        policy = autonomy_registry.get(self.descriptor.name)
        needs_hitl = policy.requires_hitl(rec.confidence) or rec.requires_hitl
        if not needs_hitl:
            state["decision"] = HITLDecision.APPROVE.value
            return state

        item = await hitl_broker.enqueue(
            agent=self.descriptor.name,
            recommendation=rec,
            context=state.get("context") or {},
            urgency=state.get("input", {}).get("urgency", 3),
            impact=state.get("input", {}).get("impact", 3),
        )
        state["hitl_item_id"] = str(item.id)
        # For async flows we record pending; execution happens when operator decides.
        state["decision"] = "pending"
        return state

    # -- execution ---------------------------------------------------------

    async def _execute_if_allowed(self, state: AgentState) -> AgentState:
        if state.get("decision") != HITLDecision.APPROVE.value:
            return state
        rec = state.get("recommendation")
        if rec is None or not rec.tool_calls:
            return state
        policy = autonomy_registry.get(self.descriptor.name)
        if policy.level < AutonomyLevel.L1_ONE_CLICK:
            return state
        # Re-execute approved tool calls as the applied action.
        results: list[ToolResult] = []
        for call in rec.tool_calls:
            results.append(await tool_vault.call(call.tool, call.args))
        state["tool_results"] = (state.get("tool_results") or []) + results
        return state

    # -- public entry ------------------------------------------------------

    async def run(self, payload: dict[str, Any]) -> AgentRun:
        run = AgentRun(agent=self.descriptor.name, input=payload)
        start = datetime.now(timezone.utc)
        state: AgentState = {"input": payload, "context": {}, "tool_results": []}
        try:
            final = await self._graph.ainvoke(state)
            rec = final.get("recommendation")
            run.recommendation = rec
            run.output = {k: v for k, v in final.items() if k != "recommendation"}
            run.status = "succeeded"
            if rec is not None:
                run.eval_score = eval_harness.score_recommendation(
                    self.descriptor.name, rec
                )
        except Exception as exc:  # pragma: no cover
            log.exception("agent.run_failed", agent=self.descriptor.name)
            run.status = "failed"
            run.output = {"error": str(exc)}
        finally:
            run.finished_at = datetime.now(timezone.utc)
            run.duration_ms = int(
                (run.finished_at - start).total_seconds() * 1000
            )
        return run
