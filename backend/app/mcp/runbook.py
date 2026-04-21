"""mcp-runbook — search, execute, propose new runbooks."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.mcp.base import MCPServer, tool
from app.models.schemas import AutonomyLevel


class RunbookMCP(MCPServer):
    name = "mcp-runbook"
    description = "Search, execute, and author runbooks."

    _BOOKS: list[dict[str, Any]] = [
        {
            "id": "RB-checkout-errors",
            "title": "Checkout HTTP 500 surge",
            "service": "checkout",
            "tags": ["checkout", "5xx", "canary"],
            "steps": [
                {"n": 1, "do": "Confirm error rate in Datadog"},
                {"n": 2, "do": "Check last change in deployer"},
                {"n": 3, "do": "Rollback canary if change < 30 min old"},
                {"n": 4, "do": "Verify error rate returns < 0.5%"},
            ],
            "success_rate": 0.91,
        },
        {
            "id": "RB-db-connections",
            "title": "DB connection pool exhaustion",
            "service": "orders-db",
            "tags": ["database", "pool", "connections"],
            "steps": [
                {"n": 1, "do": "Identify long-running sessions"},
                {"n": 2, "do": "Kill session pid if > 10min"},
                {"n": 3, "do": "Raise pool_size temporarily"},
                {"n": 4, "do": "Open ticket for index review"},
            ],
            "success_rate": 0.88,
        },
    ]

    @tool(
        name="search_runbook",
        description="Search the runbook library by text or service.",
        args_schema={
            "query": {"type": "string"},
            "service": {"type": "string"},
        },
        read_only=True,
    )
    async def search_runbook(
        self, query: str | None = None, service: str | None = None
    ) -> list[dict[str, Any]]:
        results = self._BOOKS
        if service:
            results = [b for b in results if b.get("service") == service]
        if query:
            q = query.lower()
            results = [
                b
                for b in results
                if q in b["title"].lower()
                or any(q in t for t in b.get("tags", []))
            ]
        return results

    @tool(
        name="execute_step",
        description="Execute a specific step of a runbook.",
        args_schema={
            "runbook_id": {"type": "string", "required": True},
            "step": {"type": "integer", "required": True},
        },
        min_autonomy=AutonomyLevel.L1_ONE_CLICK,
    )
    async def execute_step(self, runbook_id: str, step: int) -> dict[str, Any]:
        book = next((b for b in self._BOOKS if b["id"] == runbook_id), None)
        if not book:
            return {"ok": False, "error": "runbook_not_found"}
        target = next((s for s in book["steps"] if s["n"] == step), None)
        if not target:
            return {"ok": False, "error": "step_not_found"}
        return {"ok": True, "runbook_id": runbook_id, "step": target, "executed": True}

    @tool(
        name="propose_runbook",
        description="Propose a new runbook (draft) from PIR + chat transcripts.",
        args_schema={
            "title": {"type": "string", "required": True},
            "service": {"type": "string", "required": True},
            "steps": {"type": "array", "required": True},
            "tags": {"type": "array"},
        },
        min_autonomy=AutonomyLevel.L1_ONE_CLICK,
    )
    async def propose_runbook(
        self,
        title: str,
        service: str,
        steps: list[dict[str, Any]],
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        draft = {
            "id": f"RB-{str(uuid4())[:8]}",
            "title": title,
            "service": service,
            "steps": steps,
            "tags": tags or [],
            "status": "draft",
        }
        self._BOOKS.append(draft)
        return draft
