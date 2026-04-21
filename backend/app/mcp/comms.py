"""mcp-comms — Slack, Teams, email, StatusPage."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.mcp.base import MCPServer, tool
from app.models.schemas import AutonomyLevel


class CommsMCP(MCPServer):
    name = "mcp-comms"
    description = "Post to channels, open war rooms, send emails, update StatusPage."

    _SENT: list[dict[str, Any]] = []

    @tool(
        name="post_channel",
        description="Post a message to a channel (Slack/Teams).",
        args_schema={
            "channel": {"type": "string", "required": True},
            "message": {"type": "string", "required": True},
        },
        min_autonomy=AutonomyLevel.L1_ONE_CLICK,
    )
    async def post_channel(self, channel: str, message: str) -> dict[str, Any]:
        record = {
            "id": str(uuid4()),
            "channel": channel,
            "message": message,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._SENT.append(record)
        return record

    @tool(
        name="create_war_room",
        description="Create a war-room channel for a major incident.",
        args_schema={
            "incident_id": {"type": "string", "required": True},
            "title": {"type": "string", "required": True},
            "invitees": {"type": "array"},
        },
        min_autonomy=AutonomyLevel.L1_ONE_CLICK,
    )
    async def create_war_room(
        self,
        incident_id: str,
        title: str,
        invitees: list[str] | None = None,
    ) -> dict[str, Any]:
        channel = f"war-{incident_id.lower()}"
        return {
            "channel": channel,
            "title": title,
            "invitees": invitees or [],
            "url": f"https://chat.example.com/{channel}",
        }

    @tool(
        name="send_email",
        description="Send a transactional email.",
        args_schema={
            "to": {"type": "array", "required": True},
            "subject": {"type": "string", "required": True},
            "body": {"type": "string", "required": True},
        },
        min_autonomy=AutonomyLevel.L1_ONE_CLICK,
    )
    async def send_email(
        self, to: list[str], subject: str, body: str
    ) -> dict[str, Any]:
        return {"queued": True, "recipients": to, "subject": subject}

    @tool(
        name="update_statuspage",
        description="Publish an update to the public status page.",
        args_schema={
            "component": {"type": "string", "required": True},
            "status": {
                "type": "string",
                "enum": ["operational", "degraded", "partial_outage", "major_outage"],
                "required": True,
            },
            "message": {"type": "string", "required": True},
        },
        min_autonomy=AutonomyLevel.L1_ONE_CLICK,
        blast_radius={"external": True, "max_services": 5},
    )
    async def update_statuspage(
        self, component: str, status: str, message: str
    ) -> dict[str, Any]:
        return {
            "component": component,
            "status": status,
            "message": message,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
