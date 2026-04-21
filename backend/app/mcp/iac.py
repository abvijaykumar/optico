"""mcp-iac — Terraform / Pulumi plan, apply, drift detection."""
from __future__ import annotations

from typing import Any

from app.mcp.base import MCPServer, tool
from app.models.schemas import AutonomyLevel


class IaCMCP(MCPServer):
    name = "mcp-iac"
    description = "Plan, apply, and detect drift in IaC stacks."

    @tool(
        name="plan",
        description="Run a terraform/pulumi plan and summarise changes.",
        args_schema={"stack": {"type": "string", "required": True}},
        read_only=True,
    )
    async def plan(self, stack: str) -> dict[str, Any]:
        return {
            "stack": stack,
            "adds": 2, "changes": 1, "destroys": 0,
            "diff_url": f"https://iac.example.com/plans/{stack}",
        }

    @tool(
        name="apply",
        description="Apply a planned IaC change.",
        args_schema={"stack": {"type": "string", "required": True}, "plan_id": {"type": "string"}},
        min_autonomy=AutonomyLevel.L2_APPLY_WITH_REVIEW,
        blast_radius={"production": True, "max_services": 5},
    )
    async def apply(self, stack: str, plan_id: str | None = None) -> dict[str, Any]:
        return {"stack": stack, "plan_id": plan_id, "applied": True}

    @tool(
        name="detect_drift",
        description="Detect drift between IaC and live state.",
        args_schema={"stack": {"type": "string", "required": True}},
        read_only=True,
    )
    async def detect_drift(self, stack: str) -> dict[str, Any]:
        return {
            "stack": stack,
            "drifted": True,
            "findings": [
                {"resource": "aws_security_group.api", "field": "ingress[2].cidr", "live": "0.0.0.0/0", "iac": "10.0.0.0/8"},
            ],
        }
