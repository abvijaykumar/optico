"""mcp-messaging — Kafka / RabbitMQ / IBM MQ operations."""
from __future__ import annotations

from typing import Any

from app.mcp.base import MCPServer, tool
from app.models.schemas import AutonomyLevel


class MessagingMCP(MCPServer):
    name = "mcp-messaging"
    description = "Consumer lag, DLQ inspect, partition rebalance."

    @tool(name="lag", description="Consumer group lag.",
          args_schema={"group": {"type": "string", "required": True}}, read_only=True)
    async def lag(self, group: str) -> dict[str, Any]:
        return {"group": group, "total_lag": 128_000, "topics": {"orders": 80_000, "payments": 48_000}}

    @tool(name="dlq_inspect", description="Peek at DLQ messages.",
          args_schema={"queue": {"type": "string", "required": True}, "limit": {"type": "integer"}},
          read_only=True)
    async def dlq_inspect(self, queue: str, limit: int = 10) -> list[dict[str, Any]]:
        return [{"id": f"msg-{i}", "reason": "DeserializationError"} for i in range(limit)]

    @tool(name="consumer_reset", description="Reset consumer group offsets.",
          args_schema={"group": {"type": "string", "required": True}, "to": {"type": "string", "required": True}},
          min_autonomy=AutonomyLevel.L2_APPLY_WITH_REVIEW)
    async def consumer_reset(self, group: str, to: str) -> dict[str, Any]:
        return {"group": group, "to": to, "reset": True}

    @tool(name="partition_rebalance", description="Trigger partition rebalance.",
          args_schema={"topic": {"type": "string", "required": True}},
          min_autonomy=AutonomyLevel.L2_APPLY_WITH_REVIEW)
    async def partition_rebalance(self, topic: str) -> dict[str, Any]:
        return {"topic": topic, "rebalanced": True}
