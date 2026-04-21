"""mcp-network — NetBox / SolarWinds / ACL / BGP."""
from __future__ import annotations

from typing import Any

from app.mcp.base import MCPServer, tool


class NetworkMCP(MCPServer):
    name = "mcp-network"
    description = "NetBox IPAM, ACL checks, BGP state."

    @tool(name="netbox_lookup", description="Look up a device / subnet in NetBox.",
          args_schema={"query": {"type": "string", "required": True}}, read_only=True)
    async def netbox_lookup(self, query: str) -> list[dict[str, Any]]:
        return [{"name": query, "site": "us-east-1a", "role": "tor", "ip": "10.10.1.1"}]

    @tool(name="acl_check", description="Check ACL reachability between src and dst.",
          args_schema={"src": {"type": "string", "required": True}, "dst": {"type": "string", "required": True}},
          read_only=True)
    async def acl_check(self, src: str, dst: str) -> dict[str, Any]:
        return {"src": src, "dst": dst, "allowed": True, "matched_rule": "ALLOW_INT_LAN"}

    @tool(name="bgp_state", description="Report BGP neighbor state.",
          args_schema={"router": {"type": "string", "required": True}}, read_only=True)
    async def bgp_state(self, router: str) -> dict[str, Any]:
        return {"router": router, "neighbors": [{"peer": "203.0.113.1", "state": "Established", "uptime_min": 4820}]}
