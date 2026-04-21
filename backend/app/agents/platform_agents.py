"""Platform agents — CloudOptimizer, IaCDrift, OSPatching, Storage,
NetworkPolicy, CertLifecycle, BackupDR.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.agents.base import AgentBase, AgentState
from app.models.schemas import (
    AgentDescriptor,
    AgentRecommendation,
    AutonomyLevel,
    EvidenceItem,
    ToolCall,
)


class CloudOptimizerAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="cloud-optimizer-agent",
        display_name="Cloud Optimizer",
        workstream="stack",
        description="Rightsize across AWS / Azure / GCP.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-aws.rightsize_recommend", "mcp-finops.rightsizing_recommend"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-aws.rightsize_recommend", args={}),
            ToolCall(tool="mcp-finops.rightsizing_recommend", args={}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        recs = []
        for r in state.get("tool_results") or []:
            if r.ok and isinstance(r.data, list):
                recs.extend(r.data)
        saving = sum(r.get("saving_usd", r.get("monthly_saving_usd", 0)) for r in recs)
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(recs)} rightsizing candidates, est. saving ${saving}/mo.",
            action="propose_rightsizing",
            tool_calls=[],
            confidence=0.78,
            evidence=[EvidenceItem(source="rightsizing", kind="metric", payload={"items": recs})],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class IaCDriftAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="iac-drift-agent",
        display_name="IaC Drift",
        workstream="stack",
        description="Detect IaC drift; propose reconciliation plans.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-iac.detect_drift", "mcp-iac.plan"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        stack = state["input"].get("stack", "prod-network")
        state["_planned_calls"] = [
            ToolCall(tool="mcp-iac.detect_drift", args={"stack": stack}),
            ToolCall(tool="mcp-iac.plan", args={"stack": stack}),
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        drift = next((r.data for r in state.get("tool_results") or [] if r.ok and "detect_drift" in r.tool), {})
        plan = next((r.data for r in state.get("tool_results") or [] if r.ok and "/plan" in ("/" + r.tool)), {})
        drifted = drift.get("drifted", False)
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=("IaC drift detected." if drifted else "No IaC drift."),
            action="reconcile" if drifted else "noop",
            tool_calls=[],
            confidence=0.82,
            evidence=[EvidenceItem(source="iac", kind="change",
                                   payload={"drift": drift, "plan": plan})],
            requires_hitl=drifted,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class OSPatchingAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="os-patching-agent",
        display_name="OS Patching",
        workstream="stack",
        description="Schedule and track OS / container-base patching.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-hardware.redfish_inventory"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        pending = [
            {"host": "node-02", "cves": ["CVE-2026-1234", "CVE-2026-1501"], "age_days": 12},
            {"host": "node-09", "cves": ["CVE-2026-1234"], "age_days": 5},
        ]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(pending)} hosts have outstanding critical patches.",
            action="schedule_patch_wave",
            tool_calls=[],
            confidence=0.76,
            evidence=[EvidenceItem(source="patch-db", kind="change", payload={"pending": pending})],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class StorageAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="storage-agent",
        display_name="Storage",
        workstream="stack",
        description="Monitor volume growth, IOPS, snapshot policies.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-observability.query_metrics"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-observability.query_metrics",
                     args={"metric": "disk_utilisation", "service": state["input"].get("service", "orders-db"),
                           "window_minutes": 60})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "query_metrics" in r.tool), None)
        latest = (res.data.get("latest") if res and res.data else 0.5) or 0.5
        risk = latest > 0.85
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"Disk utilisation {latest:.2f}.",
            action="expand_volume" if risk else "monitor",
            tool_calls=[],
            confidence=0.74,
            evidence=[EvidenceItem(source="metrics", kind="metric", payload={"latest": latest})],
            requires_hitl=risk,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class NetworkPolicyAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="net-policy-agent",
        display_name="Network Policy",
        workstream="stack",
        description="Ensure least-privilege network policies per namespace / service.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-network.acl_check", "mcp-security.policy_check"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-security.policy_check",
                     args={"resource": state["input"].get("resource", "ns/checkout")})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        res = next((r for r in state.get("tool_results") or [] if r.ok and "policy_check" in r.tool), None)
        data = res.data if res and res.data else {}
        compliant = data.get("compliant", True)
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=("Policies compliant." if compliant else f"Policy violations: {data.get('violations')}."),
            action="tighten_policy" if not compliant else "noop",
            tool_calls=[],
            confidence=0.8,
            evidence=[EvidenceItem(source="opa", kind="change", payload=data)],
            requires_hitl=not compliant,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class CertificateAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="cert-agent",
        display_name="Certificate Lifecycle",
        workstream="stack",
        description="Track cert expirations and propose rotations.",
        autonomy_level=AutonomyLevel.L1_ONE_CLICK,
        tools=["mcp-security.vault_read"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = []
        return state

    async def decide(self, state: AgentState) -> AgentState:
        expiring = [
            {"host": "api.optico.com", "expires": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()},
            {"host": "checkout.optico.com", "expires": (datetime.now(timezone.utc) + timedelta(days=45)).isoformat()},
        ]
        urgent = [c for c in expiring if "2026" in c["expires"][:4]]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(expiring)} certs tracked, {len(urgent)} expiring within window.",
            action="schedule_rotation",
            tool_calls=[],
            confidence=0.82,
            evidence=[EvidenceItem(source="vault", kind="change", payload={"expiring": expiring})],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state


class BackupDRAgent(AgentBase):
    descriptor = AgentDescriptor(
        name="backup-dr-agent",
        display_name="Backup / DR",
        workstream="stack",
        description="Verify backup freshness + DR runbook readiness.",
        autonomy_level=AutonomyLevel.L0_RECOMMEND,
        tools=["mcp-runbook.search_runbook"],
    )

    async def plan(self, state: AgentState) -> AgentState:
        state["_planned_calls"] = [
            ToolCall(tool="mcp-runbook.search_runbook", args={"query": "DR"})
        ]
        return state

    async def decide(self, state: AgentState) -> AgentState:
        backups = [
            {"service": "orders-db", "last_backup": "2026-04-21T03:00:00Z", "rpo_minutes": 60},
            {"service": "payments", "last_backup": "2026-04-20T03:00:00Z", "rpo_minutes": 1440},
        ]
        stale = [b for b in backups if b["rpo_minutes"] > 120]
        state["recommendation"] = AgentRecommendation(
            agent=self.descriptor.name,
            summary=f"{len(stale)} backups exceed RPO.",
            action="trigger_backup" if stale else "noop",
            tool_calls=[],
            confidence=0.74,
            evidence=[EvidenceItem(source="backup-ledger", kind="change", payload={"backups": backups})],
            requires_hitl=True,
            autonomy_level=self.descriptor.autonomy_level,
        )
        return state
