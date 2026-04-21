"""Hardware agents — Health, DiskFailure, Firmware, NetworkFabric, PowerThermal."""
from __future__ import annotations

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class HardwareHealthAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="hw-health-agent",
        display_name="Hardware Health",
        workstream="stack",
        description="Roll up IPMI / Redfish / SNMP signals into per-host health.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-hardware.ipmi_status", "mcp-hardware.redfish_inventory"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        host = state["input"].get("host", "node-01")
        state["_planned_calls"] = [
            ToolCall(tool="mcp-hardware.ipmi_status", args={"host": host}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        host = state["input"].get("host", "node-01")
        res = next((r for r in state.get("tool_results") or [] if r.ok and "ipmi_status" in r.tool), None)
        temp = (res.data.get("cpu_temp_c") if res and res.data else 0) or 0
        unhealthy = temp > 75
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Host {host}: CPU {temp}°C — {'ALERT' if unhealthy else 'OK'}.",
            action="open_incident" if unhealthy else "noop",
            tool_calls=[],
            confidence=0.85,
            evidence=[EvidenceItem(source="ipmi", kind="metric",
                                   payload={"cpu_temp_c": temp, "unhealthy": unhealthy})],
            requires_hitl=unhealthy,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class DiskFailurePredictionAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="disk-failure-agent",
        display_name="Disk Failure Prediction",
        workstream="stack",
        description="Predict disk failures from SMART signals.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-hardware.smart_disk"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-hardware.smart_disk",
                     args={"host": state["input"].get("host", "node-01"), "disk": "sda"})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "smart_disk" in r.tool), None)
        smart = res.data if res and res.data else {}
        failing = smart.get("smart_status") == "FAILING" or smart.get("reallocated_sectors", 0) > 5
        prob = 0.9 if failing else 0.07
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Disk failure probability: {prob:.0%}.",
            action="replace_disk" if failing else "monitor",
            tool_calls=[],
            confidence=0.78,
            evidence=[EvidenceItem(source="smart", kind="metric", payload=smart)],
            requires_hitl=failing,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class FirmwareLifecycleAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="firmware-agent",
        display_name="Firmware Lifecycle",
        workstream="stack",
        description="Track firmware levels against vendor advisories.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-hardware.redfish_inventory"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-hardware.redfish_inventory",
                     args={"host": state["input"].get("host", "node-01")})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "redfish_inventory" in r.tool), None)
        inv = res.data if res and res.data else {}
        outdated = inv.get("bios", "0") < "2.14.0"
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"BIOS {inv.get('bios')} — {'update available' if outdated else 'current'}.",
            action="schedule_firmware_update" if outdated else "noop",
            tool_calls=[],
            confidence=0.8,
            evidence=[EvidenceItem(source="redfish", kind="change", payload=inv)],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class NetworkFabricAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="net-fabric-agent",
        display_name="Network Fabric",
        workstream="stack",
        description="Detect switch/port/BGP anomalies.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-network.bgp_state", "mcp-hardware.switch_port_state"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-network.bgp_state", args={"router": state["input"].get("router", "core-1")})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "bgp_state" in r.tool), None)
        bgp = res.data if res and res.data else {}
        any_down = any(n.get("state") != "Established" for n in bgp.get("neighbors", []))
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary="BGP peer down." if any_down else "BGP fabric healthy.",
            action="open_incident" if any_down else "noop",
            tool_calls=[],
            confidence=0.82,
            evidence=[EvidenceItem(source="bgp", kind="metric", payload=bgp)],
            requires_hitl=any_down,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class PowerThermalAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="power-thermal-agent",
        display_name="Power & Thermal",
        workstream="stack",
        description="Rack-level power / thermal risk detection.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-hardware.ipmi_status"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-hardware.ipmi_status", args={"host": state["input"].get("host", "rack-a1")})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "ipmi_status" in r.tool), None)
        status = res.data if res and res.data else {}
        temp = status.get("cpu_temp_c", 0) or 0
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Rack thermal {temp}°C.",
            action="noop",
            tool_calls=[],
            confidence=0.7,
            evidence=[EvidenceItem(source="ipmi", kind="metric", payload=status)],
            requires_hitl=temp > 80,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
