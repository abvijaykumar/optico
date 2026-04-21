"""mcp-azure — VM / AKS / SQL / Monitor."""
from __future__ import annotations

from typing import Any

from app.mcp.base import MCPServer, tool


class AzureMCP(MCPServer):
    name = "mcp-azure"
    description = "Azure VM / AKS / SQL / Monitor."

    @tool(name="list_vms", description="List Azure VMs.",
          args_schema={"subscription": {"type": "string"}}, read_only=True)
    async def list_vms(self, subscription: str = "default") -> list[dict[str, Any]]:
        return [{"id": f"vm-{i}", "size": "Standard_D4s_v5", "state": "running"} for i in range(3)]

    @tool(name="aks_nodes", description="List AKS node pools.",
          args_schema={"cluster": {"type": "string", "required": True}}, read_only=True)
    async def aks_nodes(self, cluster: str) -> list[dict[str, Any]]:
        return [{"pool": "system", "nodes": 3}, {"pool": "user", "nodes": 6}]

    @tool(name="monitor_alerts", description="Active Azure Monitor alerts.",
          args_schema={}, read_only=True)
    async def monitor_alerts(self) -> list[dict[str, Any]]:
        return [{"id": "az-0021", "rule": "MemoryHigh", "severity": "Sev2", "target": "vm-1"}]
