"""Neo4j schema for the unified knowledge graph.

Nodes:
  - Service, Host, Cluster, Database, Application
  - Incident, Alert, Change, Runbook, KEDBEntry, PIR
  - Team, Person, Agent, Model

Relationships:
  - (:Service)-[:DEPENDS_ON]->(:Service)
  - (:Service)-[:RUNS_ON]->(:Host|Cluster)
  - (:Service)-[:OWNED_BY]->(:Team)
  - (:Incident)-[:AFFECTS]->(:Service)
  - (:Incident)-[:TRIGGERED_BY]->(:Change)
  - (:Alert)-[:FIRED_FOR]->(:Service)
  - (:Alert)-[:GROUPED_INTO]->(:Incident)
  - (:Runbook)-[:RESOLVES]->(:Incident|KEDBEntry)
  - (:Agent)-[:ACTED_ON]->(:Incident|Change)
  - (:KEDBEntry)-[:MATCHES]->(:Alert)
"""

KG_SCHEMA_CYPHER: list[str] = [
    "CREATE CONSTRAINT service_name IF NOT EXISTS FOR (s:Service) REQUIRE s.name IS UNIQUE",
    "CREATE CONSTRAINT host_name IF NOT EXISTS FOR (h:Host) REQUIRE h.name IS UNIQUE",
    "CREATE CONSTRAINT cluster_name IF NOT EXISTS FOR (c:Cluster) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT alert_id IF NOT EXISTS FOR (a:Alert) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT change_id IF NOT EXISTS FOR (c:Change) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT runbook_id IF NOT EXISTS FOR (r:Runbook) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT kedb_id IF NOT EXISTS FOR (k:KEDBEntry) REQUIRE k.id IS UNIQUE",
    "CREATE CONSTRAINT agent_name IF NOT EXISTS FOR (a:Agent) REQUIRE a.name IS UNIQUE",
    "CREATE INDEX service_tier IF NOT EXISTS FOR (s:Service) ON (s.tier)",
    "CREATE INDEX incident_severity IF NOT EXISTS FOR (i:Incident) ON (i.severity)",
]


# Seed data used when Neo4j is unavailable — the in-memory graph mirrors the
# same shape so agents work identically in both modes.
SEED_GRAPH: dict = {
    "nodes": [
        {"label": "Service", "props": {"name": "checkout", "tier": "1", "owner": "payments-team"}},
        {"label": "Service", "props": {"name": "orders-api", "tier": "1", "owner": "orders-team"}},
        {"label": "Service", "props": {"name": "orders-db", "tier": "1", "owner": "platform-team"}},
        {"label": "Service", "props": {"name": "payments", "tier": "1", "owner": "payments-team"}},
        {"label": "Service", "props": {"name": "notifications", "tier": "2", "owner": "growth-team"}},
        {"label": "Cluster", "props": {"name": "prod-us-east-1", "provider": "aws"}},
        {"label": "Team", "props": {"name": "payments-team"}},
        {"label": "Team", "props": {"name": "orders-team"}},
        {"label": "Team", "props": {"name": "platform-team"}},
    ],
    "relationships": [
        {"from": ("Service", "checkout"), "to": ("Service", "orders-api"), "type": "DEPENDS_ON"},
        {"from": ("Service", "orders-api"), "to": ("Service", "orders-db"), "type": "DEPENDS_ON"},
        {"from": ("Service", "checkout"), "to": ("Service", "payments"), "type": "DEPENDS_ON"},
        {"from": ("Service", "checkout"), "to": ("Cluster", "prod-us-east-1"), "type": "RUNS_ON"},
        {"from": ("Service", "orders-api"), "to": ("Cluster", "prod-us-east-1"), "type": "RUNS_ON"},
        {"from": ("Service", "checkout"), "to": ("Team", "payments-team"), "type": "OWNED_BY"},
        {"from": ("Service", "orders-api"), "to": ("Team", "orders-team"), "type": "OWNED_BY"},
    ],
}
