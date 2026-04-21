"""Agent roster + direct run endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.agents.registry import agent_registry
from app.agents.supervisor import supervisor
from app.data.store import data_store
from app.governance.autonomy import autonomy_registry
from app.models.schemas import AgentDescriptor

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[dict[str, Any]])
async def list_agents() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for descriptor in agent_registry.list():
        policy = autonomy_registry.get(descriptor.name)
        out.append(
            {
                **descriptor.model_dump(mode="json"),
                "policy": {
                    "level": policy.level,
                    "runs": policy.runs,
                    "accuracy": round(policy.accuracy, 3),
                    "calibration_error": round(policy.calibration_error, 3),
                    "shadow_mode": policy.shadow_mode,
                    "kill_switch": policy.kill_switch,
                },
            }
        )
    return out


@router.post("/{agent_name}/run")
async def run_agent(agent_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        agent = agent_registry.get(agent_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    run = await agent.run(payload)
    data_store.log_audit(
        {"event": "agent_run", "agent": agent_name, "status": run.status}
    )
    return run.model_dump(mode="json")


@router.post("/supervisor/alert")
async def supervisor_alert(alert: dict[str, Any]) -> dict[str, Any]:
    """Feed an alert to the Supervisor — drives the full incident workflow."""
    result = await supervisor.handle_alert(alert)
    data_store.log_audit(
        {"event": "supervisor_alert", "service": alert.get("service")}
    )
    return result
