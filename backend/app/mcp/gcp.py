"""mcp-gcp — GCE / GKE / CloudSQL / Ops."""
from __future__ import annotations

from typing import Any

from app.mcp.base import MCPServer, tool


class GCPMCP(MCPServer):
    name = "mcp-gcp"
    description = "GCP GCE / GKE / CloudSQL / Cloud Monitoring."

    @tool(name="list_gce", description="List GCE instances.",
          args_schema={"project": {"type": "string"}}, read_only=True)
    async def list_gce(self, project: str = "optico-prod") -> list[dict[str, Any]]:
        return [{"name": f"gce-{i}", "zone": "us-central1-a", "status": "RUNNING"} for i in range(2)]

    @tool(name="gke_clusters", description="List GKE clusters.",
          args_schema={}, read_only=True)
    async def gke_clusters(self) -> list[dict[str, Any]]:
        return [{"name": "prod-gke", "location": "us-central1", "node_count": 12}]

    @tool(name="ops_alerts", description="Active GCP Operations alerts.",
          args_schema={}, read_only=True)
    async def ops_alerts(self) -> list[dict[str, Any]]:
        return [{"id": "gcp-a1", "policy": "LoadBalancer5xx", "state": "open"}]
