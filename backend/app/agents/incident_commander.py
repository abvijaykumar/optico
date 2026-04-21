"""Incident Commander Agent — orchestrates the response.

Opens the war room, assigns roles, drives status updates, and hands off
to RCA and Remediation agents.
"""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class IncidentCommanderAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="incident-commander",
        display_name="Incident Commander",
        workstream="incident",
        description="Drives major incident response — war room, comms, role assignment.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=[
            "mcp-comms.create_war_room",
            "mcp-comms.post_channel",
            "mcp-comms.update_statuspage",
        ],
        blast_radius={"external": True, "max_services": 10},
    )

    async def plan(self, state: AgentState) -> AgentState:
        incident = state["input"].get("incident", {})
        state["_planned_calls"] = []  # all actions deferred to decide/approve
        state["context"] = {"incident": incident}
        return state

    async def decide(self, state: AgentState) -> AgentState:
        incident = state["input"].get("incident", {})
        severity = incident.get("severity", "SEV2")
        incident_id = str(incident.get("id", "INC-UNKNOWN"))
        title = incident.get("title", "Unnamed incident")
        services = ", ".join(incident.get("services") or [])

        calls = [
            ToolCall(
                tool="mcp-comms.create_war_room",
                args={
                    "incident_id": incident_id,
                    "title": f"{severity}: {title}",
                    "invitees": ["@sre-oncall", "@payments-oncall"],
                },
            ),
            ToolCall(
                tool="mcp-comms.post_channel",
                args={
                    "channel": f"war-{incident_id.lower()}",
                    "message": (
                        f":rotating_light: {severity} incident opened on {services}. "
                        f"Roles: IC=agent, Ops=@sre-oncall, Comms=@comms-lead."
                    ),
                },
            ),
        ]
        if severity == "SEV1":
            calls.append(
                ToolCall(
                    tool="mcp-comms.update_statuspage",
                    args={
                        "component": services or "platform",
                        "status": "partial_outage",
                        "message": "We are investigating elevated errors.",
                    },
                )
            )

        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=(
                f"Opening war-room for {severity} {title} on {services}. "
                f"{'Statuspage update drafted.' if severity == 'SEV1' else ''}"
            ),
            action="open_war_room",
            tool_calls=calls,
            confidence=0.9,
            evidence=[
                EvidenceItem(
                    source="incident", kind="change", payload={"incident": incident}
                )
            ],
            requires_hitl=severity == "SEV1",
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
