"""Multi-cluster federation.

Each cluster is an isolated Optico control-plane instance with its own
KG, orchestrator, and MCP vault. The federation layer:

* routes cross-cluster queries via Trino-like federation (signed HTTP)
* replicates KG nodes that must be globally visible (services, SLOs)
* isolates tenant data (cluster-of-record)
* pins the FedRAMP enclave to its own cluster + its own key material
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any


@dataclass
class Cluster:
    id: str
    name: str
    region: str
    profile: str  # "standard", "fedramp", "eu-data-residency"
    tenant_ids: list[str] = field(default_factory=list)
    endpoint: str | None = None
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Security — filled on registration only if profile == "fedramp"
    enclave: bool = False
    kms_key_arn: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "region": self.region,
            "profile": self.profile,
            "tenant_ids": self.tenant_ids,
            "endpoint": self.endpoint,
            "registered_at": self.registered_at.isoformat(),
            "enclave": self.enclave,
            "kms_key_arn": self.kms_key_arn,
        }


class FederationRegistry:
    def __init__(self) -> None:
        self._clusters: dict[str, Cluster] = {}
        self._lock = RLock()
        # Seed with demo clusters so the console has content out of the box.
        self.register(Cluster(
            id="us-east-1-prod", name="US East (prod)", region="us-east-1",
            profile="standard", tenant_ids=["retail", "b2b"],
            endpoint="https://optico.us-east-1.example.com",
        ))
        self.register(Cluster(
            id="eu-west-1-prod", name="EU West (prod)", region="eu-west-1",
            profile="eu-data-residency", tenant_ids=["eu-retail"],
            endpoint="https://optico.eu-west-1.example.com",
        ))
        self.register(Cluster(
            id="fedramp-govcloud", name="FedRAMP (GovCloud)", region="us-gov-west-1",
            profile="fedramp", tenant_ids=["gov-a"],
            endpoint="https://optico.gov.example.com",
            enclave=True,
            kms_key_arn="arn:aws-us-gov:kms:us-gov-west-1:000000000000:key/optico-enclave",
        ))

    def register(self, cluster: Cluster) -> Cluster:
        with self._lock:
            self._clusters[cluster.id] = cluster
        return cluster

    def get(self, cluster_id: str) -> Cluster | None:
        return self._clusters.get(cluster_id)

    def list(self) -> list[Cluster]:
        with self._lock:
            return list(self._clusters.values())

    def route(self, tenant_id: str) -> Cluster | None:
        """Return the cluster-of-record for a tenant."""
        with self._lock:
            for c in self._clusters.values():
                if tenant_id in c.tenant_ids:
                    return c
        return None


federation = FederationRegistry()
