"""Lightweight in-memory data store.

Real deployments swap this for SQLAlchemy+Postgres (schemas already
match). The API surface below is what the REST routes depend on.
"""
from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.models.schemas import (
    Change,
    Incident,
    IncidentStatus,
    KEDBEntry,
    Runbook,
)

log = get_logger(__name__)


class DataStore:
    def __init__(self) -> None:
        self._incidents: dict[UUID, Incident] = {}
        self._changes: dict[UUID, Change] = {}
        self._runbooks: dict[UUID, Runbook] = {}
        self._kedb: dict[UUID, KEDBEntry] = {}
        self._audit: list[dict[str, Any]] = []
        self._lock = RLock()

    # -- incidents ---------------------------------------------------------

    def upsert_incident(self, incident: Incident) -> Incident:
        with self._lock:
            incident.updated_at = datetime.now(timezone.utc)
            self._incidents[incident.id] = incident
        return incident

    def get_incident(self, id: UUID) -> Incident | None:
        return self._incidents.get(id)

    def list_incidents(
        self, status: IncidentStatus | None = None, limit: int = 100
    ) -> list[Incident]:
        with self._lock:
            items = list(self._incidents.values())
        if status:
            items = [i for i in items if i.status == status]
        items.sort(key=lambda i: i.created_at, reverse=True)
        return items[:limit]

    # -- changes -----------------------------------------------------------

    def upsert_change(self, change: Change) -> Change:
        with self._lock:
            self._changes[change.id] = change
        return change

    def list_changes(self, limit: int = 100) -> list[Change]:
        with self._lock:
            items = list(self._changes.values())
        items.sort(key=lambda c: c.created_at, reverse=True)
        return items[:limit]

    # -- runbooks ----------------------------------------------------------

    def upsert_runbook(self, rb: Runbook) -> Runbook:
        with self._lock:
            self._runbooks[rb.id] = rb
        return rb

    def list_runbooks(self) -> list[Runbook]:
        with self._lock:
            return list(self._runbooks.values())

    # -- KEDB --------------------------------------------------------------

    def upsert_kedb(self, entry: KEDBEntry) -> KEDBEntry:
        with self._lock:
            self._kedb[entry.id] = entry
        return entry

    def list_kedb(self) -> list[KEDBEntry]:
        with self._lock:
            return list(self._kedb.values())

    # -- audit log ---------------------------------------------------------

    def log_audit(self, event: dict[str, Any]) -> None:
        with self._lock:
            event = {"ts": datetime.now(timezone.utc).isoformat(), **event}
            self._audit.append(event)
        log.info("audit", **{k: v for k, v in event.items() if k != "ts"})

    def list_audit(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock:
            return list(reversed(self._audit[-limit:]))


data_store = DataStore()
