# Optico Architecture Notes

## Runtime shape

The backend is a single FastAPI app with a LangGraph orchestrator. All
sub-systems are in-process so the local dev story is a single
`uvicorn` command. Production deployments split:

* **Gateway / API** — FastAPI
* **Agent workers** — LangGraph + Celery or Temporal per agent pod
* **Tool Vault MCP processes** — one per domain (observability / itsm
  / k8s / db / cloud / …). Each speaks MCP over stdio or HTTP; the
  `ToolVault` class is identical.
* **KG** — Neo4j cluster
* **Ledger** — Postgres for incidents, changes, audit
* **Stream** — Kafka for event sourcing; Redis for pub/sub + cache
* **Lake / warehouse** — Iceberg on S3 + DuckDB/ClickHouse/Trino

## Per-agent lifecycle

```
alert  →  Supervisor (LangGraph)
           ↓
         Triage  →  decides incident skeleton
           ↓
         Correlation → clusters
           ↓
         Incident Commander (SEV1 only) → war room + statuspage
           ↓
         RCA → hypothesis tree
           ↓
         Remediation → proposes / (L2+) executes
           ↓
         PIR → drafts post-incident write-up
           ↓
         KEDB → extracts reusable lesson
```

Every step writes back to the KG and is audit-logged.

## Autonomy graduation

```
runs ≥ 30  AND  accuracy ≥ 0.95  AND  calibration_error ≤ 0.10
AND  no_regressions_in_30d  →  promotable
```

A human must click **Promote** from the Governance console. Promotion
is a durable event in the audit log.

## HITL contract

* **Urgency × Impact** is the sort key.
* **Blast radius** in the recommendation's tool calls is computed
  against the agent's descriptor limits.
* **Evidence chain** is verbatim from the KG + tool results. Operators
  can expand raw JSON for any evidence item.

## Policy enforcement

The `policy_engine` is the in-process analogue of an OPA sidecar; it
checks tool calls for autonomy level, rate limits, read-only status,
and blast-radius caps. Swap in OPA by reimplementing `PolicyEngine`
with the same `evaluate()` signature — no agent changes.
