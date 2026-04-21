"""mcp-db — database operations (Oracle / Postgres / Mongo / DB2)."""
from __future__ import annotations

from typing import Any

from app.mcp.base import MCPServer, tool
from app.models.schemas import AutonomyLevel


class DBMCP(MCPServer):
    name = "mcp-db"
    description = "DB queries, plans, index advisor, vacuum, failover."

    @tool(name="run_query", description="Run a read-only SELECT.",
          args_schema={"db": {"type": "string", "required": True}, "sql": {"type": "string", "required": True}},
          read_only=True)
    async def run_query(self, db: str, sql: str) -> dict[str, Any]:
        return {"db": db, "sql": sql, "rows": [{"count": 42}]}

    @tool(name="explain_plan", description="Return query plan.",
          args_schema={"db": {"type": "string", "required": True}, "sql": {"type": "string", "required": True}},
          read_only=True)
    async def explain_plan(self, db: str, sql: str) -> dict[str, Any]:
        return {"db": db, "plan": [{"op": "Seq Scan", "cost": 10234}, {"op": "Hash Join", "cost": 4102}]}

    @tool(name="index_advisor", description="Suggest indexes for slow queries.",
          args_schema={"db": {"type": "string", "required": True}}, read_only=True)
    async def index_advisor(self, db: str) -> list[dict[str, Any]]:
        return [{"table": "orders", "columns": ["customer_id", "created_at"], "benefit_ms": 820}]

    @tool(name="vacuum", description="Run VACUUM / ANALYZE.",
          args_schema={"db": {"type": "string", "required": True}, "table": {"type": "string"}},
          min_autonomy=AutonomyLevel.L2_APPLY_WITH_REVIEW)
    async def vacuum(self, db: str, table: str | None = None) -> dict[str, Any]:
        return {"db": db, "table": table or "ALL", "ok": True}

    @tool(name="failover", description="Promote the replica; last-resort action.",
          args_schema={"db": {"type": "string", "required": True}},
          min_autonomy=AutonomyLevel.L2_APPLY_WITH_REVIEW,
          blast_radius={"production": True, "max_services": 20})
    async def failover(self, db: str) -> dict[str, Any]:
        return {"db": db, "failed_over": True}
