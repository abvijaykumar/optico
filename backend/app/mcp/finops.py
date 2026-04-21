"""mcp-finops — spend queries, budgets, rightsizing."""
from __future__ import annotations

from typing import Any

from app.mcp.base import MCPServer, tool


class FinOpsMCP(MCPServer):
    name = "mcp-finops"
    description = "Spend, budgets, rightsizing recommendations."

    @tool(name="spend_query", description="Query spend by service / tag / window.",
          args_schema={"service": {"type": "string"}, "window_days": {"type": "integer"}},
          read_only=True)
    async def spend_query(self, service: str | None = None, window_days: int = 30) -> dict[str, Any]:
        return {
            "service": service or "all",
            "window_days": window_days,
            "spend_usd": 42_500 if service else 286_400,
            "breakdown": [
                {"resource": "compute", "usd": 128_200},
                {"resource": "storage", "usd": 74_900},
                {"resource": "network", "usd": 56_000},
                {"resource": "managed_services", "usd": 27_300},
            ],
        }

    @tool(name="budget_alert", description="Check budget thresholds.",
          args_schema={}, read_only=True)
    async def budget_alert(self) -> list[dict[str, Any]]:
        return [{"budget": "prod-monthly", "limit_usd": 300_000, "used_usd": 286_400, "pct": 0.95}]

    @tool(name="rightsizing_recommend", description="Cross-cloud rightsizing list.",
          args_schema={}, read_only=True)
    async def rightsizing_recommend(self) -> list[dict[str, Any]]:
        return [
            {"resource": "i-0abc", "saving_usd": 42, "risk": "low"},
            {"resource": "orders-db", "saving_usd": 310, "risk": "medium"},
        ]
