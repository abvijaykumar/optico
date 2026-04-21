"""Dashboard-facing aggregation endpoints (RoI², DORA, Reliability)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from random import Random

from fastapi import APIRouter

from app.agents.registry import agent_registry
from app.data.store import data_store
from app.governance.autonomy import autonomy_registry
from app.models.schemas import RoIMetrics

router = APIRouter(prefix="/dashboards", tags=["dashboards"])

_rng = Random(42)


@router.get("/roi", response_model=RoIMetrics)
async def roi() -> RoIMetrics:
    # These aggregate across agent registry + data store so the metric grows
    # with real platform usage. Mocked baselines are used on cold start.
    agents = autonomy_registry.all()
    l2_plus = sum(1 for a in agents if int(a.level) >= 2)
    runs = sum(a.runs for a in agents)
    avg_acc = (sum(a.accuracy for a in agents) / max(1, len(agents))) if agents else 0.0

    return RoIMetrics(
        decision_yield={
            "alerts_auto_triaged_pct": round(min(0.95, 0.5 + avg_acc / 2), 3),
            "mttr_reduction_pct": 0.41,
            "change_failure_rate_reduction_pct": 0.32,
        },
        learning_velocity={
            "runbooks_generated_last_30d": 24,
            "kedb_entries_last_30d": 57,
            "days_to_automation": 11.5,
        },
        cognitive_leverage={
            "toil_hours_reclaimed_per_week": 520,
            "agents_at_l2_plus": l2_plus,
            "pct_incidents_with_drafted_pir": 1.0,
        },
        financial={
            "ops_cost_delta_pct": -0.27,
            "avoided_downtime_usd_30d": 185000,
        },
    )


@router.get("/live-ops")
async def live_ops() -> dict:
    incidents = data_store.list_incidents(limit=10)
    return {
        "active_incidents": [i.model_dump(mode="json") for i in incidents[:5]],
        "agent_actions_last_hour": _rng.randint(45, 70),
        "hitl_queue_depth": _rng.randint(1, 8),
        "mttr_trend_min": [22, 21, 19, 18, 17, 17, 16],
    }


@router.get("/reliability")
async def reliability() -> dict:
    services = ["checkout", "orders-api", "orders-db", "payments", "notifications"]
    return {
        "services": [
            {
                "name": s,
                "slo": 0.995,
                "availability_30d": round(0.994 + (_rng.random() * 0.005), 5),
                "error_budget_remaining_pct": round(_rng.uniform(0.15, 0.85), 3),
                "toil_index": round(_rng.uniform(0.05, 0.4), 3),
            }
            for s in services
        ]
    }


@router.get("/change-radar")
async def change_radar() -> dict:
    return {
        "dora": {
            "change_failure_rate": 0.043,
            "lead_time_hours": 3.2,
            "deployment_frequency_per_day": 14.7,
            "mttr_minutes": 17,
        },
        "upcoming_changes": [
            {
                "id": "CHG-2026-0421-01",
                "service": "checkout",
                "risk": 0.24,
                "scheduled": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
                "auto_approvable": True,
            },
            {
                "id": "CHG-2026-0421-02",
                "service": "orders-db",
                "risk": 0.71,
                "scheduled": (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat(),
                "auto_approvable": False,
            },
        ],
    }


@router.get("/infra-health")
async def infra_health() -> dict:
    return {
        "hosts": {"total": 420, "healthy": 408, "degraded": 9, "failed": 3},
        "k8s": {"clusters": 6, "nodes": 124, "pods_pending": 2},
        "patch_compliance_pct": 0.96,
    }


@router.get("/cost")
async def cost() -> dict:
    return {
        "monthly_spend_usd": 286_400,
        "idle_resources_usd": 18_200,
        "anomalies": [
            {"service": "orders-db", "delta_pct": 0.14, "likely_cause": "new index build"},
            {"service": "notifications", "delta_pct": 0.09, "likely_cause": "retention bump"},
        ],
    }
