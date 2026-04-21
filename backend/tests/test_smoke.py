"""Smoke tests — verify the full agent loop works without external services."""
from __future__ import annotations

import asyncio

import pytest

from app.agents.registry import agent_registry, register_all_agents
from app.agents.supervisor import supervisor
from app.mcp import register_all_servers


@pytest.fixture(scope="module", autouse=True)
def setup():
    register_all_servers()
    register_all_agents()


@pytest.mark.asyncio
async def test_triage_agent_runs():
    agent = agent_registry.get("triage-agent")
    run = await agent.run(
        {
            "alert": {
                "source": "datadog",
                "service": "checkout",
                "signal": "HighErrorRate",
                "severity": "SEV2",
                "fingerprint": "fp-001",
            }
        }
    )
    assert run.status == "succeeded"
    assert run.recommendation is not None


@pytest.mark.asyncio
async def test_supervisor_end_to_end():
    result = await supervisor.handle_alert(
        {
            "source": "datadog",
            "service": "checkout",
            "signal": "HighErrorRate",
            "severity": "SEV2",
            "fingerprint": "fp-002",
        }
    )
    assert result["incident"] is not None
    assert result["triage"] is not None
    # Phase 4 predictor should have been chained after KEDB.
    assert result["predictor"] is not None


@pytest.mark.asyncio
async def test_phase4_agents_runnable():
    for name in (
        "major-incident-predictor",
        "finops-agent",
        "compliance-agent",
        "sec-correlation-agent",
        "kg-maintenance-agent",
        "documentation-agent",
    ):
        agent = agent_registry.get(name)
        run = await agent.run({})
        assert run.status == "succeeded"
        assert run.recommendation is not None


@pytest.mark.asyncio
async def test_stack_agents_runnable():
    for name in (
        "hw-health-agent",
        "disk-failure-agent",
        "dba-agent",
        "broker-agent",
        "apm-agent",
        "trace-agent",
        "cloud-optimizer-agent",
        "iac-drift-agent",
    ):
        agent = agent_registry.get(name)
        run = await agent.run({})
        assert run.status == "succeeded"
