"""Pydantic schemas — shared across API and agents."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Governance / autonomy
# ---------------------------------------------------------------------------


class AutonomyLevel(int, Enum):
    L0_RECOMMEND = 0          # Suggest only, human executes
    L1_ONE_CLICK = 1          # Prepared action, one-click apply
    L2_APPLY_WITH_REVIEW = 2  # Auto-apply, synchronous human review
    L3_APPLY_NOTIFY = 3       # Auto-apply, async notification
    L4_AUTONOMOUS = 4         # Fully autonomous within blast-radius policy


class Severity(str, Enum):
    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"
    SEV4 = "SEV4"


class IncidentStatus(str, Enum):
    NEW = "new"
    TRIAGING = "triaging"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ChangeStatus(str, Enum):
    DRAFT = "draft"
    SCORED = "scored"
    CAB_PENDING = "cab_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"


class HITLDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"
    ESCALATE = "escalate"


# ---------------------------------------------------------------------------
# Core domain entities
# ---------------------------------------------------------------------------


class Alert(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    source: str
    service: str
    signal: str
    message: str
    severity: Severity = Severity.SEV3
    fingerprint: str
    labels: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)


class Incident(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    title: str
    summary: str
    severity: Severity = Severity.SEV3
    status: IncidentStatus = IncidentStatus.NEW
    services: list[str] = Field(default_factory=list)
    alerts: list[UUID] = Field(default_factory=list)
    linked_changes: list[UUID] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    commander: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    mttr_seconds: int | None = None


class Change(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    title: str
    service: str
    change_type: str  # deploy, config, infra, db
    risk_score: float = 0.0
    risk_factors: list[str] = Field(default_factory=list)
    status: ChangeStatus = ChangeStatus.DRAFT
    requested_by: str
    scheduled_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class Runbook(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    slug: str
    title: str
    service: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    success_rate: float = 0.0
    last_run: datetime | None = None


class KEDBEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    symptoms: list[str] = Field(default_factory=list)
    root_cause: str
    workaround: str
    permanent_fix: str | None = None
    tags: list[str] = Field(default_factory=list)
    hit_count: int = 0
    created_at: datetime = Field(default_factory=_utcnow)


class CMDBNode(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    ci_type: str  # service, host, db, cluster, app
    name: str
    owner: str | None = None
    tier: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    relationships: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent framework
# ---------------------------------------------------------------------------


class AgentDescriptor(BaseModel):
    name: str
    display_name: str
    workstream: str  # platform, incident, release, sre, stack, analytics
    description: str
    autonomy_level: AutonomyLevel = AutonomyLevel.L0_RECOMMEND
    tools: list[str] = Field(default_factory=list)
    blast_radius: dict[str, Any] = Field(default_factory=dict)
    owner: str | None = None


class ToolCall(BaseModel):
    tool: str
    args: dict[str, Any]
    reason: str | None = None


class EvidenceItem(BaseModel):
    source: str
    kind: str  # metric, log, trace, change, kg_node
    url: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    weight: float = 1.0


class AgentRecommendation(BaseModel):
    """What an agent produces — explainable, auditable."""

    id: UUID = Field(default_factory=uuid4)
    agent: str
    summary: str
    action: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    confidence: float = 0.0
    evidence: list[EvidenceItem] = Field(default_factory=list)
    requires_hitl: bool = True
    autonomy_level: AutonomyLevel = AutonomyLevel.L0_RECOMMEND
    created_at: datetime = Field(default_factory=_utcnow)


class AgentRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    agent: str
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    recommendation: AgentRecommendation | None = None
    status: str = "running"  # running, succeeded, failed, escalated
    started_at: datetime = Field(default_factory=_utcnow)
    finished_at: datetime | None = None
    duration_ms: int | None = None
    eval_score: float | None = None


# ---------------------------------------------------------------------------
# HITL
# ---------------------------------------------------------------------------


class HITLItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    agent: str
    recommendation: AgentRecommendation
    context: dict[str, Any] = Field(default_factory=dict)
    urgency: int = 3          # 1 = highest
    impact: int = 3           # 1 = highest
    created_at: datetime = Field(default_factory=_utcnow)
    decided_at: datetime | None = None
    decision: HITLDecision | None = None
    decided_by: str | None = None
    decision_notes: str | None = None


# ---------------------------------------------------------------------------
# Dashboard / RoI²
# ---------------------------------------------------------------------------


class RoIMetrics(BaseModel):
    decision_yield: dict[str, float]
    learning_velocity: dict[str, float]
    cognitive_leverage: dict[str, float]
    financial: dict[str, float]
    generated_at: datetime = Field(default_factory=_utcnow)
