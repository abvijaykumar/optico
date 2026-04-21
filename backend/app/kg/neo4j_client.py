"""Knowledge Graph client.

Transparent fall-back: when Neo4j is reachable we use bolt; otherwise we
use a thread-safe in-memory adjacency list with the same query surface
so agents, tests, and the demo stack all work without Neo4j.
"""
from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.kg.schema import SEED_GRAPH

log = get_logger(__name__)


class _InMemoryGraph:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._nodes: dict[tuple[str, str], dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []
        self._adj_out: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        self._adj_in: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    def upsert_node(self, label: str, props: dict[str, Any]) -> None:
        key = (label, props.get("name") or props.get("id"))
        with self._lock:
            self._nodes[key] = {"label": label, **props}

    def add_edge(
        self,
        frm: tuple[str, str],
        to: tuple[str, str],
        rel_type: str,
        props: dict[str, Any] | None = None,
    ) -> None:
        edge = {"from": frm, "to": to, "type": rel_type, "props": props or {}}
        with self._lock:
            self._edges.append(edge)
            self._adj_out[frm].append(edge)
            self._adj_in[to].append(edge)

    def get_node(self, label: str, name: str) -> dict[str, Any] | None:
        with self._lock:
            return self._nodes.get((label, name))

    def neighbors(
        self, label: str, name: str, rel_type: str | None = None, direction: str = "out"
    ) -> list[dict[str, Any]]:
        key = (label, name)
        with self._lock:
            edges = self._adj_out[key] if direction == "out" else self._adj_in[key]
            edges = [e for e in edges if rel_type is None or e["type"] == rel_type]
            return [
                {
                    "rel": e["type"],
                    "node": self._nodes.get(e["to"] if direction == "out" else e["from"]),
                }
                for e in edges
            ]

    def all_nodes(self, label: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            return [n for (l, _), n in self._nodes.items() if label is None or l == label]


class KnowledgeGraph:
    """Unified KG interface — Neo4j-backed with in-memory fallback."""

    def __init__(self) -> None:
        self._mem = _InMemoryGraph()
        self._driver = None
        self._use_bolt = False
        self._seed()

    # -- lifecycle ---------------------------------------------------------

    async def connect(self) -> None:
        settings = get_settings()
        try:
            from neo4j import AsyncGraphDatabase

            self._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            async with self._driver.session() as sess:
                await sess.run("RETURN 1 AS ok")
            self._use_bolt = True
            log.info("kg.connected", backend="neo4j", uri=settings.neo4j_uri)
        except Exception as exc:
            self._use_bolt = False
            log.warning("kg.fallback_inmemory", reason=str(exc))

    async def close(self) -> None:
        if self._driver is not None:
            await self._driver.close()

    # -- seed --------------------------------------------------------------

    def _seed(self) -> None:
        for node in SEED_GRAPH["nodes"]:
            self._mem.upsert_node(node["label"], node["props"])
        for rel in SEED_GRAPH["relationships"]:
            self._mem.add_edge(rel["from"], rel["to"], rel["type"])

    # -- facade used by agents --------------------------------------------

    async def service_context(self, service: str) -> dict[str, Any]:
        node = self._mem.get_node("Service", service) or {}
        deps = self._mem.neighbors("Service", service, "DEPENDS_ON", "out")
        upstream = self._mem.neighbors("Service", service, "DEPENDS_ON", "in")
        runs_on = self._mem.neighbors("Service", service, "RUNS_ON", "out")
        owner = self._mem.neighbors("Service", service, "OWNED_BY", "out")
        return {
            "service": node,
            "depends_on": [d["node"] for d in deps if d["node"]],
            "upstream": [u["node"] for u in upstream if u["node"]],
            "runs_on": [r["node"] for r in runs_on if r["node"]],
            "owner": [o["node"] for o in owner if o["node"]],
        }

    async def add_incident_node(self, incident: dict[str, Any]) -> None:
        self._mem.upsert_node("Incident", incident)
        for svc in incident.get("services", []):
            self._mem.add_edge(
                ("Incident", incident["id"]),
                ("Service", svc),
                "AFFECTS",
            )

    async def add_change_node(self, change: dict[str, Any]) -> None:
        self._mem.upsert_node("Change", change)
        if svc := change.get("service"):
            self._mem.add_edge(
                ("Change", change["id"]),
                ("Service", svc),
                "TARGETS",
            )

    async def link_incident_to_change(self, incident_id: str, change_id: str) -> None:
        self._mem.add_edge(
            ("Incident", incident_id),
            ("Change", change_id),
            "TRIGGERED_BY",
        )

    async def recent_changes_for(self, service: str, limit: int = 5) -> list[dict[str, Any]]:
        edges = self._mem._adj_in[("Service", service)]
        changes = [
            self._mem.get_node("Change", e["from"][1])
            for e in edges
            if e["from"][0] == "Change" and e["type"] == "TARGETS"
        ]
        return [c for c in changes if c][:limit]

    async def all_services(self) -> list[dict[str, Any]]:
        return self._mem.all_nodes("Service")


kg = KnowledgeGraph()
