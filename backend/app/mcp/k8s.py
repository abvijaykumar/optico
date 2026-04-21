"""mcp-k8s — Kubernetes operations (kubectl / helm / argocd)."""
from __future__ import annotations

from typing import Any

from app.mcp.base import MCPServer, tool
from app.models.schemas import AutonomyLevel


class K8sMCP(MCPServer):
    name = "mcp-k8s"
    description = "Kubernetes operations — pods, deployments, nodes, argocd."

    @tool(
        name="list_pods",
        description="List pods in a namespace.",
        args_schema={"namespace": {"type": "string", "required": True}},
        read_only=True,
    )
    async def list_pods(self, namespace: str) -> list[dict[str, Any]]:
        return [
            {"name": f"{namespace}-app-{i}", "status": "Running", "restarts": 0}
            for i in range(3)
        ] + [
            {"name": f"{namespace}-app-3", "status": "CrashLoopBackOff", "restarts": 7},
        ]

    @tool(
        name="describe_deployment",
        description="Describe a deployment.",
        args_schema={
            "namespace": {"type": "string", "required": True},
            "name": {"type": "string", "required": True},
        },
        read_only=True,
    )
    async def describe_deployment(self, namespace: str, name: str) -> dict[str, Any]:
        return {
            "namespace": namespace,
            "name": name,
            "replicas": 3,
            "available": 2,
            "image": f"registry/{name}:1.2.3",
            "events": [{"reason": "FailedScheduling", "count": 1}],
        }

    @tool(
        name="cordon",
        description="Cordon a node (prevent scheduling).",
        args_schema={"node": {"type": "string", "required": True}},
        min_autonomy=AutonomyLevel.L2_APPLY_WITH_REVIEW,
        blast_radius={"max_services": 5},
    )
    async def cordon(self, node: str) -> dict[str, Any]:
        return {"node": node, "cordoned": True}

    @tool(
        name="drain",
        description="Drain a node (evict pods).",
        args_schema={"node": {"type": "string", "required": True}},
        min_autonomy=AutonomyLevel.L2_APPLY_WITH_REVIEW,
        blast_radius={"max_services": 5},
    )
    async def drain(self, node: str) -> dict[str, Any]:
        return {"node": node, "drained": True}

    @tool(
        name="scale_deployment",
        description="Scale a deployment to a target replica count.",
        args_schema={
            "namespace": {"type": "string", "required": True},
            "name": {"type": "string", "required": True},
            "replicas": {"type": "integer", "required": True},
        },
        min_autonomy=AutonomyLevel.L2_APPLY_WITH_REVIEW,
    )
    async def scale_deployment(
        self, namespace: str, name: str, replicas: int
    ) -> dict[str, Any]:
        return {"namespace": namespace, "name": name, "replicas": replicas}
