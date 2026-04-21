"""mcp-gitops — Argo CD / Flux style GitOps reconciliation."""
from __future__ import annotations

from typing import Any

from app.mcp.base import MCPServer, tool
from app.models.schemas import AutonomyLevel


class GitOpsMCP(MCPServer):
    name = "mcp-gitops"
    description = "Reconcile git-declared state to runtime clusters."

    _APPS: list[dict[str, Any]] = [
        {"name": "checkout", "revision": "main@9f3c1a", "synced": True, "healthy": True},
        {"name": "orders-api", "revision": "main@bcd421", "synced": False, "healthy": True},
        {"name": "notifications", "revision": "main@77aa23", "synced": True, "healthy": False},
    ]

    @tool(
        name="diff_state",
        description="Diff desired (git) vs live state for an app.",
        args_schema={"app": {"type": "string", "required": True}},
        read_only=True,
    )
    async def diff_state(self, app: str) -> dict[str, Any]:
        record = next((a for a in self._APPS if a["name"] == app), None)
        if not record:
            return {"app": app, "error": "unknown"}
        return {
            "app": app,
            "in_sync": record["synced"],
            "drift": [] if record["synced"] else [{"field": "replicas", "git": 4, "live": 3}],
        }

    @tool(
        name="sync_app",
        description="Trigger a sync/reconcile for the named app.",
        args_schema={"app": {"type": "string", "required": True}},
        min_autonomy=AutonomyLevel.L2_APPLY_WITH_REVIEW,
        blast_radius={"max_services": 1},
    )
    async def sync_app(self, app: str) -> dict[str, Any]:
        for a in self._APPS:
            if a["name"] == app:
                a["synced"] = True
        return {"app": app, "synced": True}

    @tool(
        name="reconcile",
        description="Reconcile all known apps.",
        args_schema={},
        min_autonomy=AutonomyLevel.L2_APPLY_WITH_REVIEW,
        blast_radius={"max_services": 20},
    )
    async def reconcile(self) -> dict[str, Any]:
        for a in self._APPS:
            a["synced"] = True
        return {"count": len(self._APPS)}
