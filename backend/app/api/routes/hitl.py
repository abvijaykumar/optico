"""HITL queue + WebSocket stream."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.hitl.broker import hitl_broker
from app.models.schemas import HITLDecision, HITLItem

router = APIRouter(prefix="/hitl", tags=["hitl"])


@router.get("/queue", response_model=list[HITLItem])
async def list_queue(include_decided: bool = False) -> list[HITLItem]:
    return hitl_broker.list_queue(include_decided=include_decided)


@router.get("/{item_id}", response_model=HITLItem)
async def get_item(item_id: UUID) -> HITLItem:
    item = hitl_broker.get(item_id)
    if not item:
        raise HTTPException(404, "hitl item not found")
    return item


@router.post("/{item_id}/decide", response_model=HITLItem)
async def decide(item_id: UUID, body: dict[str, Any]) -> HITLItem:
    try:
        decision = HITLDecision(body.get("decision"))
    except ValueError:
        raise HTTPException(400, "invalid decision")
    return await hitl_broker.decide(
        item_id,
        decision=decision,
        decided_by=body.get("decided_by") or "anonymous",
        notes=body.get("notes"),
    )


@router.websocket("/stream")
async def stream(ws: WebSocket) -> None:
    await ws.accept()
    queue = hitl_broker.subscribe()
    try:
        while True:
            event = await queue.get()
            await ws.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        hitl_broker.unsubscribe(queue)
