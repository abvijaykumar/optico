"""mcp-analytics — warehouse queries, dashboard publishing."""
from __future__ import annotations

from typing import Any

from app.mcp.base import MCPServer, tool


class AnalyticsMCP(MCPServer):
    name = "mcp-analytics"
    description = "Run notebooks, query warehouse, publish dashboards."

    @tool(
        name="query_warehouse",
        description="Run a SQL query against the analytics warehouse.",
        args_schema={"sql": {"type": "string", "required": True}},
        read_only=True,
    )
    async def query_warehouse(self, sql: str) -> dict[str, Any]:
        # Deterministic mock — return aggregate by service.
        return {
            "sql": sql,
            "rows": [
                {"service": "checkout", "incidents_30d": 12, "mttr_min": 18},
                {"service": "orders-api", "incidents_30d": 8, "mttr_min": 22},
                {"service": "payments", "incidents_30d": 4, "mttr_min": 14},
            ],
        }

    @tool(
        name="run_notebook",
        description="Execute a parameterised notebook.",
        args_schema={
            "notebook": {"type": "string", "required": True},
            "params": {"type": "object"},
        },
    )
    async def run_notebook(
        self, notebook: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return {"notebook": notebook, "params": params or {}, "status": "succeeded"}

    @tool(
        name="publish_dashboard",
        description="Publish or refresh a dashboard.",
        args_schema={"dashboard_id": {"type": "string", "required": True}},
    )
    async def publish_dashboard(self, dashboard_id: str) -> dict[str, Any]:
        return {"dashboard_id": dashboard_id, "published": True}
