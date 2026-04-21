"""Change / release endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.agents.registry import agent_registry
from app.data.store import data_store
from app.kg.neo4j_client import kg
from app.models.schemas import Change

router = APIRouter(prefix="/changes", tags=["changes"])


@router.get("", response_model=list[Change])
async def list_changes() -> list[Change]:
    return data_store.list_changes()


@router.post("", response_model=Change)
async def create_change(change: Change) -> Change:
    saved = data_store.upsert_change(change)
    await kg.add_change_node(saved.model_dump(mode="json"))
    return saved


@router.post("/{change_id}/score", response_model=dict[str, Any])
async def score_change(change_id: str) -> dict[str, Any]:
    change = next(
        (c for c in data_store.list_changes() if str(c.id) == change_id),
        None,
    )
    if not change:
        raise HTTPException(404, "change not found")
    agent = agent_registry.get("change-risk-agent")
    run = await agent.run({"change": change.model_dump(mode="json")})
    return run.model_dump(mode="json")
