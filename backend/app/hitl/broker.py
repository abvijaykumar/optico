"""Human-in-the-loop broker.

One queue per operator, ranked by urgency × impact, with:
  - pub/sub stream for UI push
  - approve / reject / edit / escalate decision API
  - event channel for agent resume (LangGraph interruptible workflows)
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.models.schemas import (
    AgentRecommendation,
    HITLDecision,
    HITLItem,
)

log = get_logger(__name__)


class HITLBroker:
    def __init__(self) -> None:
        self._items: dict[UUID, HITLItem] = {}
        self._lock = RLock()
        self._subscribers: list[asyncio.Queue[dict[str, Any]]] = []
        self._decision_events: dict[UUID, asyncio.Event] = defaultdict(asyncio.Event)

    # -- enqueue / resolve -------------------------------------------------

    async def enqueue(
        self,
        *,
        agent: str,
        recommendation: AgentRecommendation,
        context: dict[str, Any] | None = None,
        urgency: int = 3,
        impact: int = 3,
    ) -> HITLItem:
        item = HITLItem(
            agent=agent,
            recommendation=recommendation,
            context=context or {},
            urgency=urgency,
            impact=impact,
        )
        with self._lock:
            self._items[item.id] = item
        await self._broadcast({"type": "hitl.enqueued", "item": item.model_dump(mode="json")})
        log.info("hitl.enqueued", agent=agent, id=str(item.id))
        return item

    async def decide(
        self,
        item_id: UUID,
        *,
        decision: HITLDecision,
        decided_by: str,
        notes: str | None = None,
        edited_recommendation: AgentRecommendation | None = None,
    ) -> HITLItem:
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                raise KeyError(f"HITL item {item_id} not found")
            if item.decision is not None:
                raise ValueError(f"HITL item {item_id} already decided")
            item.decision = decision
            item.decided_by = decided_by
            item.decision_notes = notes
            item.decided_at = datetime.now(timezone.utc)
            if edited_recommendation:
                item.recommendation = edited_recommendation
        # signal waiters
        evt = self._decision_events[item_id]
        evt.set()
        await self._broadcast(
            {"type": "hitl.decided", "item": item.model_dump(mode="json")}
        )
        log.info(
            "hitl.decided", id=str(item_id), decision=decision.value, by=decided_by
        )
        return item

    async def wait_for_decision(
        self, item_id: UUID, timeout_s: float = 600.0
    ) -> HITLItem:
        evt = self._decision_events[item_id]
        try:
            await asyncio.wait_for(evt.wait(), timeout=timeout_s)
        except asyncio.TimeoutError:
            log.warning("hitl.timeout", id=str(item_id))
            return self._items[item_id]
        return self._items[item_id]

    # -- queries -----------------------------------------------------------

    def list_queue(
        self, include_decided: bool = False, limit: int = 100
    ) -> list[HITLItem]:
        with self._lock:
            items = list(self._items.values())
        if not include_decided:
            items = [i for i in items if i.decision is None]
        items.sort(
            key=lambda i: (
                i.urgency,
                i.impact,
                -(i.created_at.timestamp()),
            )
        )
        return items[:limit]

    def get(self, item_id: UUID) -> HITLItem | None:
        with self._lock:
            return self._items.get(item_id)

    # -- realtime subscribers ---------------------------------------------

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any]]) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    async def _broadcast(self, event: dict[str, Any]) -> None:
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                log.warning("hitl.subscriber_slow", dropped=True)


hitl_broker = HITLBroker()
