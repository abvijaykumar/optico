"""Eval harness — scores every agent run for autonomy graduation."""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Callable

from app.core.logging import get_logger
from app.governance.autonomy import autonomy_registry
from app.models.schemas import AgentRecommendation

log = get_logger(__name__)


@dataclass
class EvalCase:
    name: str
    input: dict[str, Any]
    expected: dict[str, Any]
    scorer: Callable[[AgentRecommendation, dict[str, Any]], float]
    weight: float = 1.0


@dataclass
class EvalResult:
    case: str
    score: float
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)


class EvalHarness:
    """Scores AgentRecommendations and feeds the autonomy registry."""

    def __init__(self) -> None:
        self._cases: dict[str, list[EvalCase]] = {}
        self._results: list[tuple[str, EvalResult]] = []
        self._lock = RLock()

    def register_cases(self, agent: str, cases: list[EvalCase]) -> None:
        with self._lock:
            self._cases.setdefault(agent, []).extend(cases)
        log.info("eval.registered", agent=agent, count=len(cases))

    def score_recommendation(
        self,
        agent: str,
        recommendation: AgentRecommendation,
        ground_truth: dict[str, Any] | None = None,
    ) -> float:
        """Score a single recommendation.

        When no ground truth is provided we fall back to a heuristic that
        rewards evidence density, tool-call grounding, and confidence
        calibration. This mirrors `vigil.ai` weak-supervision scoring.
        """
        confidence = recommendation.confidence
        evidence_score = min(1.0, len(recommendation.evidence) / 3)
        tool_score = min(1.0, len(recommendation.tool_calls) / 2)
        base = 0.4 * evidence_score + 0.3 * tool_score + 0.3 * confidence

        if ground_truth:
            expected_action = ground_truth.get("action")
            if expected_action:
                base *= 1.0 if recommendation.action == expected_action else 0.5

        autonomy_registry.record_run(
            agent,
            success=base >= 0.7,
            regression=False,
            confidence=confidence,
            ground_truth_score=base,
        )
        log.info(
            "eval.scored",
            agent=agent,
            score=round(base, 3),
            confidence=round(confidence, 3),
        )
        return round(base, 3)


eval_harness = EvalHarness()
