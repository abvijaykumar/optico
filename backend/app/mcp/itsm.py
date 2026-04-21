"""mcp-itsm — ServiceNow / Jira / PagerDuty abstraction."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.mcp.base import MCPServer, tool
from app.models.schemas import AutonomyLevel


class ITSMMCP(MCPServer):
    name = "mcp-itsm"
    description = "Create incidents, link changes, search KEDB, manage problems."

    _INCIDENTS: dict[str, dict[str, Any]] = {}
    _KEDB: list[dict[str, Any]] = [
        {
            "id": "KEDB-102",
            "title": "Checkout 500s after deploy — env var drift",
            "symptoms": ["HTTP 500 /api/orders", "config hash mismatch"],
            "root_cause": "Missing env var in canary pod",
            "workaround": "kubectl set env deploy/checkout ORDERS_DB=...",
        },
        {
            "id": "KEDB-087",
            "title": "DB connection pool exhaustion on monthly reporting",
            "symptoms": ["connection timeout", "active connections > pool size"],
            "root_cause": "Long-running report holds connections",
            "workaround": "Kill report session; bump pool temporarily",
        },
    ]

    @tool(
        name="create_incident",
        description="Create a new incident ticket.",
        args_schema={
            "title": {"type": "string", "required": True},
            "severity": {"type": "string", "required": True},
            "service": {"type": "string", "required": True},
            "summary": {"type": "string"},
        },
        min_autonomy=AutonomyLevel.L1_ONE_CLICK,
    )
    async def create_incident(
        self,
        title: str,
        severity: str,
        service: str,
        summary: str | None = None,
    ) -> dict[str, Any]:
        ticket_id = f"INC-{str(uuid4())[:8]}"
        record = {
            "id": ticket_id,
            "title": title,
            "severity": severity,
            "service": service,
            "summary": summary,
            "status": "new",
        }
        self._INCIDENTS[ticket_id] = record
        return record

    @tool(
        name="update_incident",
        description="Update fields on an existing incident.",
        args_schema={
            "id": {"type": "string", "required": True},
            "fields": {"type": "object", "required": True},
        },
        min_autonomy=AutonomyLevel.L1_ONE_CLICK,
    )
    async def update_incident(self, id: str, fields: dict[str, Any]) -> dict[str, Any]:
        record = self._INCIDENTS.setdefault(id, {"id": id})
        record.update(fields)
        return record

    @tool(
        name="link_change",
        description="Link a change ticket to an incident.",
        args_schema={
            "incident_id": {"type": "string", "required": True},
            "change_id": {"type": "string", "required": True},
        },
        min_autonomy=AutonomyLevel.L1_ONE_CLICK,
    )
    async def link_change(self, incident_id: str, change_id: str) -> dict[str, Any]:
        record = self._INCIDENTS.setdefault(incident_id, {"id": incident_id})
        record.setdefault("linked_changes", []).append(change_id)
        return record

    @tool(
        name="search_kedb",
        description="Search the Known Error Database by symptom.",
        args_schema={"query": {"type": "string", "required": True}},
        read_only=True,
    )
    async def search_kedb(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        return [
            entry
            for entry in self._KEDB
            if any(q in sym.lower() for sym in entry["symptoms"])
            or q in entry["title"].lower()
        ]

    @tool(
        name="create_problem",
        description="Escalate an incident to a Problem record.",
        args_schema={
            "title": {"type": "string", "required": True},
            "related_incidents": {"type": "array"},
        },
        min_autonomy=AutonomyLevel.L1_ONE_CLICK,
    )
    async def create_problem(
        self, title: str, related_incidents: list[str] | None = None
    ) -> dict[str, Any]:
        return {
            "id": f"PRB-{str(uuid4())[:8]}",
            "title": title,
            "related_incidents": related_incidents or [],
            "status": "open",
        }
