"""mcp-aws — AWS control-plane + CloudWatch read surface.

Mock implementation. Production swaps in boto3/aioboto3 behind the
same tool signatures.
"""
from __future__ import annotations

from typing import Any

from app.mcp.base import MCPServer, tool
from app.models.schemas import AutonomyLevel


class AWSMCP(MCPServer):
    name = "mcp-aws"
    description = "AWS EC2 / EKS / RDS / S3 / CloudWatch."

    @tool(name="list_ec2", description="List EC2 instances.",
          args_schema={"region": {"type": "string"}}, read_only=True)
    async def list_ec2(self, region: str = "us-east-1") -> list[dict[str, Any]]:
        return [{"id": f"i-0{i:x}", "type": "m6i.large", "state": "running", "region": region}
                for i in range(4)]

    @tool(name="describe_rds", description="Describe RDS instances.",
          args_schema={"region": {"type": "string"}}, read_only=True)
    async def describe_rds(self, region: str = "us-east-1") -> list[dict[str, Any]]:
        return [{"id": "orders-db", "engine": "postgres", "multi_az": True, "region": region}]

    @tool(name="cloudwatch_alarms", description="List CloudWatch alarms.",
          args_schema={"region": {"type": "string"}}, read_only=True)
    async def cloudwatch_alarms(self, region: str = "us-east-1") -> list[dict[str, Any]]:
        return [{"name": "HighCPU-orders-db", "state": "ALARM", "region": region}]

    @tool(name="rightsize_recommend", description="Compute Rightsizing candidates.",
          args_schema={}, read_only=True)
    async def rightsize_recommend(self) -> list[dict[str, Any]]:
        return [
            {"resource": "i-0abc", "current": "m6i.large", "recommended": "m6i.medium", "monthly_saving_usd": 42},
            {"resource": "orders-db", "current": "db.r6g.xlarge", "recommended": "db.r6g.large", "monthly_saving_usd": 310},
        ]
