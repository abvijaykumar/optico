"""Governance endpoints — autonomy policies, kill-switches, audit."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.data.store import data_store
from app.governance.autonomy import autonomy_registry

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/policies")
async def list_policies() -> list[dict]:
    return [
        {
            "agent": p.agent,
            "level": int(p.level),
            "min_confidence": p.min_confidence,
            "shadow_mode": p.shadow_mode,
            "kill_switch": p.kill_switch,
            "runs": p.runs,
            "successes": p.successes,
            "accuracy": round(p.accuracy, 3),
            "calibration_error": round(p.calibration_error, 3),
            "promoted_at": p.promoted_at.isoformat() if p.promoted_at else None,
        }
        for p in autonomy_registry.all()
    ]


@router.post("/policies/{agent}/promote")
async def promote(agent: str) -> dict:
    ok, reason = autonomy_registry.try_promote(agent)
    return {"ok": ok, "reason": reason, "level": int(autonomy_registry.get(agent).level)}


@router.post("/policies/{agent}/kill-switch")
async def toggle_kill_switch(agent: str, body: dict) -> dict:
    engaged = bool(body.get("engaged", True))
    p = autonomy_registry.set_kill_switch(agent, engaged)
    data_store.log_audit(
        {"event": "kill_switch", "agent": agent, "engaged": engaged}
    )
    return {"agent": p.agent, "kill_switch": p.kill_switch}


@router.post("/policies/{agent}/shadow-mode")
async def toggle_shadow(agent: str, body: dict) -> dict:
    engaged = bool(body.get("engaged", True))
    p = autonomy_registry.set_shadow_mode(agent, engaged)
    return {"agent": p.agent, "shadow_mode": p.shadow_mode}


@router.get("/audit")
async def audit(limit: int = 200) -> list[dict]:
    return data_store.list_audit(limit=limit)
