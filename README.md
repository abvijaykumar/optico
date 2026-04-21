# Optico — Agentic ITOps Platform

End-to-end, full-stack agentic automation for Release Management,
Incident Management, SRE, and Data Analytics — built on the `vigil.ai`
substrate (LangGraph orchestrator, MCP Tool Vault, Neo4j knowledge
graph, L0–L4 autonomy model).

> This repository is the **reference implementation** of the 60-week
> Agentic ITOps implementation plan. It ships Phase 0 (substrate) plus
> Phase 1 (incident management core) in runnable form, with stubbed
> Phase 2–4 agents that follow the same pattern so new capabilities
> plug in via the registry.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ L5 — Experience: React + IBM Carbon console                  │
├──────────────────────────────────────────────────────────────┤
│ L4 — Orchestration: LangGraph Supervisor + Domain Graphs     │
├──────────────────────────────────────────────────────────────┤
│ L3 — Agents: Triage, Correlation, RCA, Commander,            │
│              Remediation, PIR, KEDB, ChangeRisk, Release,    │
│              SLO, Capacity (all LangGraph-based)             │
├──────────────────────────────────────────────────────────────┤
│ L2 — Shared Services: MCP Tool Vault · KG (Neo4j / in-mem)   │
│      Governance (L0–L4 + kill-switch + policy) · HITL Broker │
│      Eval Harness · Audit Log                                │
├──────────────────────────────────────────────────────────────┤
│ L1 — Data: Postgres / SQLite · Redis (pub/sub, cache)        │
├──────────────────────────────────────────────────────────────┤
│ L0 — Integrations (MCP servers):                             │
│      Observability · ITSM · Comms · Runbook · CI/CD · K8s   │
│      Knowledge · Analytics (+ stubs for Cloud/DB/Net/HW)    │
└──────────────────────────────────────────────────────────────┘
```

## Repo layout

```
backend/                     Python 3.12 · FastAPI · LangChain · LangGraph
  app/
    agents/                  Specialist agents + LangGraph supervisor
    mcp/                     MCP Tool Vault + servers
    kg/                      Neo4j client with in-memory fallback
    governance/              Autonomy policy + policy engine
    hitl/                    Human-in-the-loop broker + WS stream
    eval/                    Eval harness (feeds autonomy graduation)
    data/                    In-memory / Postgres data store
    api/routes/              FastAPI routers
    core/, models/           Config, logging, pydantic schemas
frontend/                    React 18 · Vite · TypeScript · IBM Carbon
  src/pages/                 Dashboards, Ops, Platform consoles
  src/components/Layout/     Carbon shell (header + side nav)
  src/api/client.ts          Typed API client (+ WebSocket for HITL)
  src/theme/styles.scss      Carbon g100 theme + Optico overlays
docker-compose.yml           backend + frontend + neo4j + redis
```

## Quick start

### Option A — docker-compose (recommended)

```bash
docker compose up --build
# Console:  http://localhost:3000
# API:      http://localhost:8000/docs
# Neo4j:    http://localhost:7474  (neo4j / optico-dev-password)
```

### Option B — local dev

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add ANTHROPIC_API_KEY or OPENAI_API_KEY if you have one
uvicorn app.main:app --reload --port 8000

# frontend
cd ../frontend
npm install
npm run dev                 # http://localhost:3000  (proxies /api to :8000)
```

> If neither `ANTHROPIC_API_KEY` nor `OPENAI_API_KEY` is set, agents
> use a deterministic `FakeListChatModel` so the full incident flow
> runs without any external LLM. If Neo4j isn't reachable the KG
> transparently falls back to an in-memory store seeded with a
> three-service demo topology.

## Try it

1. Open **Live Ops** in the console.
2. Use **Inject a test alert** to fire e.g. `service=checkout`,
   `signal=HighErrorRate`, `severity=SEV2`.
3. Watch the Supervisor drive:
   **Triage → Correlation → (IC on SEV1) → RCA → Remediation → PIR → KEDB**.
4. Open **HITL Queue** — low-confidence recommendations land here
   with their full evidence chain. Approve / reject / escalate.
5. Open **Governance** — promote an agent from L0 → L1 after 30
   runs + accuracy criteria, or engage a kill-switch.
6. **Agent Roster** shows the roster + per-agent autonomy, accuracy,
   calibration error, flags.
7. **RoI² Scorecard** aggregates Decision Yield, Learning Velocity,
   Cognitive Leverage, Financial.

## Key design patterns

### MCP servers

```python
class ObservabilityMCP(MCPServer):
    name = "mcp-observability"

    @tool(
        name="query_metrics",
        description="Query a metric by name over a time window.",
        args_schema={...},
        read_only=True,
    )
    async def query_metrics(self, metric, service=None, window_minutes=30):
        ...
```

Every tool self-declares autonomy minimum, read-only flag, and blast
radius. The **policy engine** gates every call by autonomy level,
rate limits, and blast-radius caps before it reaches the vault.

### Agents

Every agent extends `AgentBase` and implements `plan()` + `decide()`.
`AgentBase` wires them into a LangGraph state machine with nodes for
`plan → call_tools → decide → hitl → execute`, so the HITL gate and
autonomy checks are universal.

### Supervisor

`app/agents/supervisor.py` is the top-level LangGraph that routes
alerts through the incident pipeline, short-circuits on low severity,
and branches into major-incident mode for SEV1.

### Autonomy (L0–L4)

* **L0** recommend only
* **L1** one-click apply
* **L2** apply with synchronous review
* **L3** apply with async notify
* **L4** fully autonomous within blast-radius policy

Graduation requires: ≥ 30 runs, ≥ 95% accuracy, ≤ 10% calibration
error, no regression in the last 30 days, owner sign-off. Every run
goes through the eval harness; the autonomy registry aggregates the
signal.

### HITL

Single queue, ranked by `urgency × impact`. Every item carries the
full **agent recommendation** — summary, proposed tool calls,
evidence chain, confidence. Decisions (approve / reject / edit /
escalate) are audit-logged and streamed to the UI over a WebSocket.

## Extending

### Add a new MCP server

1. Create `backend/app/mcp/<domain>.py` subclassing `MCPServer`.
2. Decorate tools with `@tool(name=..., description=..., ...)`.
3. Register it in `backend/app/mcp/loader.py`.

### Add a new agent

1. Create `backend/app/agents/<name>_agent.py` subclassing `AgentBase`.
2. Define the class-level `descriptor: AgentDescriptor`.
3. Implement `plan(state)` and `decide(state)`.
4. Register it in `backend/app/agents/registry.py`.

The Carbon console picks up new agents automatically via the
`/api/agents` endpoint; new dashboards follow the same pattern in
`frontend/src/pages/` + `App.tsx`.

## Phase alignment

| Phase | Weeks  | Shipped in this repo                                                |
| ----- | ------ | ------------------------------------------------------------------- |
| 0     | 1–8    | Full substrate (orchestrator, MCP vault, KG, HITL, eval, governance) |
| 1     | 9–20   | Triage, Correlation, RCA, IC, Remediation, PIR, KEDB                |
| 2     | 21–32  | ChangeRisk, Release, CAB, Canary, Rollback, ReleaseNotes, FeatureFlagGov, DeploymentDrift + mcp-gitops/flags/iac |
| 3     | 33–48  | **SRE**: SLO, Capacity, Toil, Chaos, DependencyMap, ReliabilityScore, RunbookAuthoring, ObservabilityCoverage. **Hardware**: Health, DiskFailure, Firmware, NetworkFabric, PowerThermal. **Platform**: CloudOptimizer, IaCDrift, OSPatching, Storage, NetworkPolicy, Certificate, Backup/DR. **Middleware**: DBA, MessageBroker, APIGateway, ServiceMesh, Cache, ContainerRuntime, LoadBalancer. **Application**: APM, LogAnalysis, DistributedTrace, RUM, Synthetic, FeaturePerf, SessionReplay. + mcp-aws/azure/gcp/db/messaging/hardware/network/k8s |
| 4     | 49–60  | MajorIncidentPredictor, FinOps, Compliance, SecurityCorrelation, KGMaintenance, Documentation + mcp-security/finops + **multi-cluster federation + tenant isolation + FedRAMP-ready enclave** |

Each phase extends the same registry and MCP vault — no bespoke
stacks per agent. The console exposes every addition via generic
views (Agent Roster, Tool Vault, Governance) plus dedicated pages
for Full-stack Health, Risk Posture, Predictive Ops, Federation &
Tenants, and FedRAMP Compliance.

### Agent count

~45 specialist agents across 6 workstreams:

* **incident** — Triage, Correlation, RCA, Commander, Remediation, PIR, KEDB
* **release** — ChangeRisk, Release, CAB, Canary, Rollback, ReleaseNotes, FeatureFlagGov, DeploymentDrift
* **sre** — SLO, Capacity, Toil, Chaos, DependencyMap, ReliabilityScore, RunbookAuthoring, ObservabilityCoverage
* **stack** — 24 agents across Hardware / Platform / Middleware / Application
* **analytics** — MajorIncidentPredictor, FinOps, Compliance, SecurityCorrelation, KGMaintenance, Documentation

### MCP vault

20 registered servers covering Observability, ITSM, Comms, Runbook,
Knowledge, CI/CD, GitOps, FeatureFlags, IaC, AWS, Azure, GCP, K8s,
DB, Messaging, Hardware, Network, Security, Analytics, FinOps.

## License

Internal reference implementation.
