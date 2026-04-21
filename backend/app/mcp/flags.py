"""mcp-flags — feature flag governance (LaunchDarkly / Unleash / Flagsmith)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.mcp.base import MCPServer, tool
from app.models.schemas import AutonomyLevel


class FlagsMCP(MCPServer):
    name = "mcp-flags"
    description = "List, toggle, and audit feature flags."

    _FLAGS: list[dict[str, Any]] = [
        {"key": "checkout.new_pricing", "enabled": True, "owner": "payments-team", "stale_days": 42},
        {"key": "orders.saga_v2", "enabled": False, "owner": "orders-team", "stale_days": 120},
        {"key": "ui.dark_mode", "enabled": True, "owner": "growth-team", "stale_days": 5},
    ]

    @tool(
        name="list_flags",
        description="List all feature flags with staleness.",
        args_schema={"owner": {"type": "string"}},
        read_only=True,
    )
    async def list_flags(self, owner: str | None = None) -> list[dict[str, Any]]:
        if owner:
            return [f for f in self._FLAGS if f["owner"] == owner]
        return self._FLAGS

    @tool(
        name="toggle_flag",
        description="Toggle a feature flag on/off.",
        args_schema={
            "key": {"type": "string", "required": True},
            "enabled": {"type": "boolean", "required": True},
        },
        min_autonomy=AutonomyLevel.L2_APPLY_WITH_REVIEW,
        blast_radius={"external": False, "max_services": 3},
    )
    async def toggle_flag(self, key: str, enabled: bool) -> dict[str, Any]:
        for f in self._FLAGS:
            if f["key"] == key:
                f["enabled"] = enabled
                return {"key": key, "enabled": enabled, "changed_at": datetime.now(timezone.utc).isoformat()}
        return {"key": key, "error": "not_found"}

    @tool(
        name="audit_flag",
        description="Return audit trail for a flag.",
        args_schema={"key": {"type": "string", "required": True}},
        read_only=True,
    )
    async def audit_flag(self, key: str) -> dict[str, Any]:
        return {
            "key": key,
            "events": [
                {"ts": "2026-04-01T09:00:00Z", "actor": "alice", "action": "create"},
                {"ts": "2026-04-05T14:12:00Z", "actor": "bob", "action": "enable"},
            ],
        }
