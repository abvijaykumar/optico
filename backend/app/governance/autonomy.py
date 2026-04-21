"""L0–L4 autonomy policy framework.

Every agent earns autonomy — it is never granted by fiat. Graduation
criteria are tracked per-agent in memory (and persisted to the audit
store in production).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import AutonomyLevel

log = get_logger(__name__)


@dataclass
class AutonomyPolicy:
    agent: str
    level: AutonomyLevel = AutonomyLevel.L0_RECOMMEND
    min_confidence: float = 0.8
    blast_radius: dict[str, Any] = field(default_factory=dict)
    shadow_mode: bool = False
    kill_switch: bool = False
    runs: int = 0
    successes: int = 0
    regressions: int = 0
    last_regression_at: datetime | None = None
    accuracy: float = 0.0
    calibration_error: float = 1.0
    promoted_at: datetime | None = None
    owner: str | None = None

    def can_auto_apply(self, confidence: float) -> bool:
        if self.kill_switch or self.shadow_mode:
            return False
        if confidence < self.min_confidence:
            return False
        return self.level >= AutonomyLevel.L1_ONE_CLICK

    def requires_hitl(self, confidence: float) -> bool:
        if self.level <= AutonomyLevel.L1_ONE_CLICK:
            return True
        if self.level == AutonomyLevel.L2_APPLY_WITH_REVIEW:
            return True
        if confidence < self.min_confidence:
            return True
        return False


class AutonomyRegistry:
    """In-memory registry of agent autonomy policies.

    In production this is backed by a durable store + audit trail. The
    API is the same — `get`, `register`, `record_run`, `try_promote`.
    """

    def __init__(self) -> None:
        self._policies: dict[str, AutonomyPolicy] = {}
        self._lock = RLock()

    # -- registration ------------------------------------------------------

    def register(self, policy: AutonomyPolicy) -> AutonomyPolicy:
        with self._lock:
            self._policies[policy.agent] = policy
        log.info("autonomy.registered", agent=policy.agent, level=policy.level)
        return policy

    def get(self, agent: str) -> AutonomyPolicy:
        with self._lock:
            if agent not in self._policies:
                self._policies[agent] = AutonomyPolicy(
                    agent=agent,
                    level=AutonomyLevel(get_settings().default_autonomy_level),
                )
            return self._policies[agent]

    def all(self) -> list[AutonomyPolicy]:
        with self._lock:
            return list(self._policies.values())

    # -- outcomes ----------------------------------------------------------

    def record_run(
        self,
        agent: str,
        *,
        success: bool,
        regression: bool = False,
        confidence: float | None = None,
        ground_truth_score: float | None = None,
    ) -> AutonomyPolicy:
        with self._lock:
            policy = self.get(agent)
            policy.runs += 1
            if success:
                policy.successes += 1
            if regression:
                policy.regressions += 1
                policy.last_regression_at = datetime.now(timezone.utc)
            policy.accuracy = (
                policy.successes / policy.runs if policy.runs else 0.0
            )
            if confidence is not None and ground_truth_score is not None:
                # Crude expected-calibration-error surrogate: |confidence - truth|
                prev = policy.calibration_error
                current = abs(confidence - ground_truth_score)
                policy.calibration_error = 0.9 * prev + 0.1 * current
            return policy

    # -- promotion ---------------------------------------------------------

    def try_promote(self, agent: str) -> tuple[bool, str]:
        settings = get_settings()
        with self._lock:
            policy = self.get(agent)
            if policy.kill_switch:
                return False, "kill_switch_engaged"
            if policy.runs < settings.autonomy_promotion_min_runs:
                return False, f"insufficient_runs ({policy.runs})"
            if policy.accuracy < settings.autonomy_promotion_min_accuracy:
                return False, f"accuracy_below_threshold ({policy.accuracy:.2f})"
            if (
                policy.calibration_error
                > settings.autonomy_promotion_max_calibration_error
            ):
                return (
                    False,
                    f"calibration_error_too_high ({policy.calibration_error:.2f})",
                )
            if (
                policy.last_regression_at
                and datetime.now(timezone.utc) - policy.last_regression_at
                < timedelta(days=30)
            ):
                return False, "regression_within_30_days"
            if policy.level >= AutonomyLevel.L4_AUTONOMOUS:
                return False, "already_max"
            new_level = AutonomyLevel(int(policy.level) + 1)
            policy.level = new_level
            policy.promoted_at = datetime.now(timezone.utc)
            log.info("autonomy.promoted", agent=agent, level=new_level.name)
            return True, f"promoted_to_{new_level.name}"

    def set_kill_switch(self, agent: str, engaged: bool) -> AutonomyPolicy:
        with self._lock:
            policy = self.get(agent)
            policy.kill_switch = engaged
        log.warning("autonomy.kill_switch", agent=agent, engaged=engaged)
        return policy

    def set_shadow_mode(self, agent: str, engaged: bool) -> AutonomyPolicy:
        with self._lock:
            policy = self.get(agent)
            policy.shadow_mode = engaged
        log.info("autonomy.shadow_mode", agent=agent, engaged=engaged)
        return policy


autonomy_registry = AutonomyRegistry()
