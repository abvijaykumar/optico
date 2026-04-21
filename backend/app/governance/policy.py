"""Policy-as-code enforcement — blast radius, rate limits, allowlists.

This is a minimal OPA-style evaluator. In production we front it with a
real OPA sidecar and compile policies from Rego; the interface below is
identical so agents don't need to change.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any

from app.core.logging import get_logger
from app.models.schemas import AutonomyLevel, ToolCall

log = get_logger(__name__)


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    obligations: dict[str, Any] | None = None


class PolicyEngine:
    """Checks tool calls against autonomy level, blast radius, rate limits."""

    # Dangerous tools always require L2+ plus explicit allowlisting.
    HIGH_RISK_TOOLS: set[str] = {
        "mcp-cicd.rollback_deploy",
        "mcp-k8s.cordon",
        "mcp-k8s.drain",
        "mcp-db.failover",
        "mcp-iac.apply",
        "mcp-flags.toggle_flag",
    }

    # Some tools are read-only and always safe.
    READ_ONLY_TOOLS: set[str] = {
        "mcp-observability.query_metrics",
        "mcp-observability.fetch_logs",
        "mcp-observability.get_traces",
        "mcp-observability.list_alerts",
        "mcp-itsm.search_kedb",
        "mcp-knowledge.search_confluence",
        "mcp-runbook.search_runbook",
        "mcp-analytics.query_warehouse",
        "mcp-finops.spend_query",
    }

    def __init__(self) -> None:
        self._rate_windows: dict[str, deque[datetime]] = defaultdict(deque)
        self._rate_limits: dict[str, tuple[int, int]] = {
            # tool -> (max_calls, window_seconds)
            "mcp-cicd.trigger_pipeline": (5, 60),
            "mcp-cicd.rollback_deploy": (3, 300),
            "mcp-comms.post_channel": (30, 60),
        }
        self._lock = RLock()

    # -- main entry --------------------------------------------------------

    def evaluate(
        self,
        *,
        agent: str,
        autonomy_level: AutonomyLevel,
        call: ToolCall,
        context: dict[str, Any] | None = None,
    ) -> PolicyDecision:
        context = context or {}

        if call.tool in self.READ_ONLY_TOOLS:
            return PolicyDecision(True, "read_only_tool")

        if call.tool in self.HIGH_RISK_TOOLS:
            if autonomy_level < AutonomyLevel.L2_APPLY_WITH_REVIEW:
                return PolicyDecision(
                    False,
                    "high_risk_requires_l2_plus",
                    obligations={"require_hitl": True},
                )

        blast = context.get("blast_radius", {})
        affected = blast.get("affected_services", [])
        if isinstance(affected, list) and len(affected) > blast.get(
            "max_services", 1
        ):
            return PolicyDecision(
                False,
                "blast_radius_exceeded",
                obligations={"require_hitl": True},
            )

        if not self._check_rate_limit(call.tool):
            return PolicyDecision(False, "rate_limit_exceeded")

        log.info(
            "policy.allowed",
            agent=agent,
            tool=call.tool,
            autonomy=autonomy_level.name,
        )
        return PolicyDecision(True, "allowed")

    # -- rate limiting -----------------------------------------------------

    def _check_rate_limit(self, tool: str) -> bool:
        limit = self._rate_limits.get(tool)
        if not limit:
            return True
        max_calls, window_s = limit
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=window_s)
        with self._lock:
            window = self._rate_windows[tool]
            while window and window[0] < cutoff:
                window.popleft()
            if len(window) >= max_calls:
                return False
            window.append(now)
        return True


policy_engine = PolicyEngine()
