"""mcp-security — SIEM, Vault, IOC lookups, policy checks."""
from __future__ import annotations

from typing import Any

from app.mcp.base import MCPServer, tool


class SecurityMCP(MCPServer):
    name = "mcp-security"
    description = "SIEM queries, Vault reads, IOC lookups, policy checks."

    @tool(name="siem_query", description="Search SIEM events.",
          args_schema={"query": {"type": "string", "required": True}, "window_minutes": {"type": "integer"}},
          read_only=True)
    async def siem_query(self, query: str, window_minutes: int = 60) -> list[dict[str, Any]]:
        return [
            {"ts": "2026-04-21T12:15:00Z", "event": "failed_login", "user": "svc_orders", "source_ip": "10.0.4.2"},
            {"ts": "2026-04-21T12:17:30Z", "event": "policy_violation", "resource": "s3://audit-logs"},
        ]

    @tool(name="vault_read", description="Read a Vault secret metadata (never value).",
          args_schema={"path": {"type": "string", "required": True}}, read_only=True)
    async def vault_read(self, path: str) -> dict[str, Any]:
        return {"path": path, "version": 3, "rotated_at": "2026-04-01T00:00:00Z"}

    @tool(name="ioc_lookup", description="Look up an IOC in threat intel.",
          args_schema={"indicator": {"type": "string", "required": True}}, read_only=True)
    async def ioc_lookup(self, indicator: str) -> dict[str, Any]:
        return {"indicator": indicator, "reputation": "malicious", "sources": ["abuse.ch", "internal"]}

    @tool(name="policy_check", description="Evaluate a resource against OPA policies.",
          args_schema={"resource": {"type": "string", "required": True}}, read_only=True)
    async def policy_check(self, resource: str) -> dict[str, Any]:
        return {"resource": resource, "compliant": False, "violations": ["PUB-S3-BUCKET"]}
