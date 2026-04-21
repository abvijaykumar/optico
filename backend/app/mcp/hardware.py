"""mcp-hardware — IPMI / Redfish / SNMP / switch ports."""
from __future__ import annotations

import random
from typing import Any

from app.mcp.base import MCPServer, tool
from app.models.schemas import AutonomyLevel


class HardwareMCP(MCPServer):
    name = "mcp-hardware"
    description = "Host health, disk SMART, firmware, switch ports."

    @tool(name="ipmi_status", description="Power / sensor state via IPMI.",
          args_schema={"host": {"type": "string", "required": True}}, read_only=True)
    async def ipmi_status(self, host: str) -> dict[str, Any]:
        return {
            "host": host, "power": "on",
            "fans_rpm": [random.randint(3000, 5000) for _ in range(4)],
            "cpu_temp_c": random.randint(45, 78),
            "psu": ["ok", "ok"],
        }

    @tool(name="redfish_inventory", description="Hardware inventory via Redfish.",
          args_schema={"host": {"type": "string", "required": True}}, read_only=True)
    async def redfish_inventory(self, host: str) -> dict[str, Any]:
        return {"host": host, "vendor": "Dell", "model": "PowerEdge R660", "bios": "2.13.0"}

    @tool(name="snmp_query", description="SNMP OID query.",
          args_schema={"host": {"type": "string", "required": True}, "oid": {"type": "string", "required": True}},
          read_only=True)
    async def snmp_query(self, host: str, oid: str) -> dict[str, Any]:
        return {"host": host, "oid": oid, "value": random.randint(0, 100)}

    @tool(name="switch_port_state", description="Get / set switch port state.",
          args_schema={"switch": {"type": "string", "required": True}, "port": {"type": "integer", "required": True}},
          min_autonomy=AutonomyLevel.L2_APPLY_WITH_REVIEW)
    async def switch_port_state(self, switch: str, port: int) -> dict[str, Any]:
        return {"switch": switch, "port": port, "state": "up", "vlan": 100}

    @tool(name="smart_disk", description="Report SMART data for a disk.",
          args_schema={"host": {"type": "string", "required": True}, "disk": {"type": "string"}},
          read_only=True)
    async def smart_disk(self, host: str, disk: str | None = None) -> dict[str, Any]:
        return {
            "host": host, "disk": disk or "sda",
            "reallocated_sectors": random.randint(0, 12),
            "pending_sectors": random.randint(0, 5),
            "temperature_c": random.randint(32, 48),
            "smart_status": "PASSED" if random.random() > 0.1 else "FAILING",
        }
