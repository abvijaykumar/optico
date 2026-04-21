"""mcp-observability — metrics, logs, traces, alerts.

Provider-agnostic interface: a real deployment wires this to
Datadog/Dynatrace/Splunk/New Relic via their SDKs. For the reference
implementation we return deterministic mock data so the full agent
graph executes end-to-end without external dependencies.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any

from app.mcp.base import MCPServer, tool
from app.models.schemas import AutonomyLevel


class ObservabilityMCP(MCPServer):
    name = "mcp-observability"
    description = "Query metrics, logs, traces, and alerts."

    @tool(
        name="query_metrics",
        description="Query a metric by name over a time window.",
        args_schema={
            "metric": {"type": "string", "required": True},
            "service": {"type": "string"},
            "window_minutes": {"type": "integer", "default": 30},
        },
        read_only=True,
    )
    async def query_metrics(
        self,
        metric: str,
        service: str | None = None,
        window_minutes: int = 30,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        points = [
            {
                "t": (now - timedelta(minutes=window_minutes - i)).isoformat(),
                "v": round(random.uniform(0.1, 1.0), 3),
            }
            for i in range(window_minutes)
        ]
        return {
            "metric": metric,
            "service": service,
            "unit": "ratio" if "error" in metric else "ms",
            "points": points,
            "latest": points[-1]["v"],
        }

    @tool(
        name="fetch_logs",
        description="Fetch recent log lines for a service with an optional filter.",
        args_schema={
            "service": {"type": "string", "required": True},
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 50},
        },
        read_only=True,
    )
    async def fetch_logs(
        self, service: str, query: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        samples = [
            "connection refused to downstream",
            "slow query detected (1.2s)",
            "circuit breaker tripped",
            "retrying upstream call",
            "HTTP 500 from /api/orders",
            "kafka consumer lag increasing",
        ]
        return [
            {
                "ts": (now - timedelta(seconds=i * 7)).isoformat(),
                "level": random.choice(["INFO", "WARN", "ERROR"]),
                "service": service,
                "message": random.choice(samples),
                "trace_id": f"t-{random.randint(10000, 99999)}",
            }
            for i in range(min(limit, 50))
        ]

    @tool(
        name="get_traces",
        description="Retrieve traces spanning a set of services.",
        args_schema={
            "service": {"type": "string", "required": True},
            "limit": {"type": "integer", "default": 10},
        },
        read_only=True,
    )
    async def get_traces(self, service: str, limit: int = 10) -> list[dict[str, Any]]:
        return [
            {
                "trace_id": f"t-{random.randint(10000, 99999)}",
                "root": service,
                "duration_ms": random.randint(120, 4300),
                "error": random.random() < 0.2,
                "spans": random.randint(3, 24),
            }
            for _ in range(limit)
        ]

    @tool(
        name="list_alerts",
        description="List active alerts, optionally filtered by service.",
        args_schema={"service": {"type": "string"}},
        read_only=True,
    )
    async def list_alerts(self, service: str | None = None) -> list[dict[str, Any]]:
        base = [
            {
                "id": "alert-001",
                "service": service or "checkout",
                "name": "HighErrorRate",
                "severity": "SEV2",
                "since": "2026-04-21T12:30:00Z",
            },
            {
                "id": "alert-002",
                "service": service or "checkout",
                "name": "LatencyP95",
                "severity": "SEV3",
                "since": "2026-04-21T12:32:00Z",
            },
        ]
        return base

    @tool(
        name="silence_alert",
        description="Silence an alert for a period (minutes).",
        args_schema={
            "alert_id": {"type": "string", "required": True},
            "minutes": {"type": "integer", "default": 30},
        },
        min_autonomy=AutonomyLevel.L1_ONE_CLICK,
        blast_radius={"max_services": 1},
    )
    async def silence_alert(self, alert_id: str, minutes: int = 30) -> dict[str, Any]:
        return {"alert_id": alert_id, "silenced_for_minutes": minutes, "ok": True}
