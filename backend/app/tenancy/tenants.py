"""Tenant (business-unit) isolation.

Every incident, change, KG node, and agent run is scoped to a tenant.
The console and API inject the tenant from the authenticated principal;
the data layer enforces row-level filtering.

This is a minimal in-memory registry — production swaps in a
Postgres-backed table behind the same interface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any


@dataclass
class Tenant:
    id: str
    name: str
    owner: str | None = None
    cluster_id: str = "us-east-1-prod"
    data_class: str = "internal"  # internal / restricted / regulated
    retention_days: int = 365
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "owner": self.owner,
            "cluster_id": self.cluster_id,
            "data_class": self.data_class,
            "retention_days": self.retention_days,
            "created_at": self.created_at.isoformat(),
        }


class TenantRegistry:
    def __init__(self) -> None:
        self._tenants: dict[str, Tenant] = {}
        self._lock = RLock()
        for t in (
            Tenant(id="retail", name="Retail BU", owner="retail-cto", cluster_id="us-east-1-prod"),
            Tenant(id="b2b", name="B2B BU", owner="b2b-vp", cluster_id="us-east-1-prod"),
            Tenant(id="eu-retail", name="Retail EU", owner="eu-cto",
                   cluster_id="eu-west-1-prod", data_class="restricted"),
            Tenant(id="gov-a", name="Gov Contract A", owner="gov-lead",
                   cluster_id="fedramp-govcloud", data_class="regulated", retention_days=2555),
        ):
            self.register(t)

    def register(self, tenant: Tenant) -> Tenant:
        with self._lock:
            self._tenants[tenant.id] = tenant
        return tenant

    def get(self, tenant_id: str) -> Tenant | None:
        return self._tenants.get(tenant_id)

    def list(self) -> list[Tenant]:
        with self._lock:
            return list(self._tenants.values())


tenants = TenantRegistry()
