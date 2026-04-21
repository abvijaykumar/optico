"""Supervisor — orchestrates specialist agents via LangGraph.

For incident-response flows the supervisor runs:

    Triage → Correlation → RCA → IncidentCommander → Remediation → PIR → KEDB

Each step emits a recommendation that is HITL-gated per autonomy policy.
The supervisor short-circuits on low-severity inputs (e.g. only runs
Triage + notify) and branches into major-incident mode for SEV1.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict  # noqa: F401
from uuid import uuid4

from app.agents.registry import agent_registry
from app.core.logging import get_logger
from app.kg.neo4j_client import kg
from app.models.schemas import AgentRun, Incident, IncidentStatus, Severity

log = get_logger(__name__)


class SupervisorState(TypedDict, total=False):
    alert: dict[str, Any]
    incident: dict[str, Any]
    triage: AgentRun | None
    correlation: AgentRun | None
    rca: AgentRun | None
    commander: AgentRun | None
    remediation: AgentRun | None
    pir: AgentRun | None
    kedb: AgentRun | None


class Supervisor:
    """Coordinates specialist agents for incident / release workflows."""

    def __init__(self) -> None:
        self._graph = self._build()

    def _build(self):
        from langgraph.graph import END, StateGraph

        g = StateGraph(dict)
        g.add_node("triage", self._run_triage)
        g.add_node("correlate", self._run_correlate)
        g.add_node("commander", self._run_commander)
        g.add_node("rca", self._run_rca)
        g.add_node("remediate", self._run_remediate)
        g.add_node("pir", self._run_pir)
        g.add_node("kedb", self._run_kedb)

        g.set_entry_point("triage")

        def after_triage(state):
            rec = state.get("triage") and state["triage"].recommendation
            severity = (state.get("incident") or {}).get("severity", "SEV3")
            if severity in ("SEV1", "SEV2"):
                return "correlate"
            return END

        g.add_conditional_edges("triage", after_triage, {"correlate": "correlate", END: END})

        def after_correlate(state):
            severity = (state.get("incident") or {}).get("severity", "SEV3")
            return "commander" if severity == "SEV1" else "rca"

        g.add_conditional_edges(
            "correlate", after_correlate, {"commander": "commander", "rca": "rca"}
        )
        g.add_edge("commander", "rca")
        g.add_edge("rca", "remediate")
        g.add_edge("remediate", "pir")
        g.add_edge("pir", "kedb")
        g.add_edge("kedb", END)
        return g.compile()

    # -- step implementations ---------------------------------------------

    async def _run_triage(self, state):
        alert = state["alert"]
        agent = agent_registry.get("triage-agent")
        run = await agent.run({"alert": alert})
        state["triage"] = run

        # Build incident skeleton from the triage recommendation.
        rec = run.recommendation
        severity = alert.get("severity", "SEV3")
        if rec and rec.evidence:
            # pull possible severity upgrade from metric payload
            for e in rec.evidence:
                latest = (e.payload or {}).get("latest")
                if latest is not None:
                    if latest > 0.5:
                        severity = "SEV1"
                    elif latest > 0.2:
                        severity = "SEV2"
        incident = Incident(
            title=alert.get("signal", "Incident"),
            summary=(rec.summary if rec else ""),
            severity=Severity(severity),
            status=IncidentStatus.TRIAGING,
            services=[alert.get("service", "unknown")],
            timeline=[
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "event": "triage_complete",
                }
            ],
        ).model_dump(mode="json")
        state["incident"] = incident
        await kg.add_incident_node(incident)
        return state

    async def _run_correlate(self, state):
        agent = agent_registry.get("correlation-agent")
        run = await agent.run({"alert": state["alert"]})
        state["correlation"] = run
        return state

    async def _run_commander(self, state):
        agent = agent_registry.get("incident-commander")
        run = await agent.run({"incident": state["incident"]})
        state["commander"] = run
        return state

    async def _run_rca(self, state):
        agent = agent_registry.get("rca-agent")
        run = await agent.run({"incident": state["incident"]})
        state["rca"] = run
        return state

    async def _run_remediate(self, state):
        agent = agent_registry.get("remediation-agent")
        top_cause = "recent_release"
        if run := state.get("rca"):
            rec = run.recommendation
            if rec and rec.evidence:
                for e in rec.evidence:
                    hyps = (e.payload or {}).get("hypotheses") or []
                    if hyps:
                        top_cause = "recent_release" if "release" in hyps[0]["cause"].lower() else "other"
                        break
        rem_run = await agent.run(
            {
                "top_cause": top_cause,
                "service": (state["incident"].get("services") or ["checkout"])[0],
            }
        )
        state["remediation"] = rem_run
        return state

    async def _run_pir(self, state):
        agent = agent_registry.get("pir-agent")
        pir_run = await agent.run(
            {
                "incident": state["incident"],
                "rca": {
                    "summary": (
                        state["rca"].recommendation.summary
                        if state.get("rca") and state["rca"].recommendation
                        else ""
                    ),
                    "top_cause": "Recent deploy introduced a regression",
                },
            }
        )
        state["pir"] = pir_run
        return state

    async def _run_kedb(self, state):
        agent = agent_registry.get("kedb-agent")
        pir_run = state.get("pir")
        symptoms = [state["alert"].get("signal", "unknown")]
        kedb_run = await agent.run(
            {
                "pir": {
                    "title": state["incident"].get("title"),
                    "symptoms": symptoms,
                    "root_cause": "Recent deploy introduced a regression",
                    "workaround": "Rollback to previous revision",
                }
            }
        )
        state["kedb"] = kedb_run
        return state

    # -- public entry -----------------------------------------------------

    async def handle_alert(self, alert: dict[str, Any]) -> dict[str, Any]:
        log.info("supervisor.alert", source=alert.get("source"), service=alert.get("service"))
        final = await self._graph.ainvoke({"alert": alert})
        return {
            "run_id": str(uuid4()),
            "incident": final.get("incident"),
            "triage": _ser(final.get("triage")),
            "correlation": _ser(final.get("correlation")),
            "commander": _ser(final.get("commander")),
            "rca": _ser(final.get("rca")),
            "remediation": _ser(final.get("remediation")),
            "pir": _ser(final.get("pir")),
            "kedb": _ser(final.get("kedb")),
        }


def _ser(run: AgentRun | None) -> dict[str, Any] | None:
    if run is None:
        return None
    return run.model_dump(mode="json")


supervisor = Supervisor()
