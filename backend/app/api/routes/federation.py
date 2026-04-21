"""Federation + Tenancy + Compliance (FedRAMP) routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.compliance.fedramp import fedramp
from app.federation.federation import federation
from app.tenancy.tenants import tenants

router = APIRouter(prefix="/federation", tags=["federation"])


@router.get("/clusters")
async def list_clusters() -> list[dict]:
    return [c.to_dict() for c in federation.list()]


@router.get("/tenants")
async def list_tenants() -> list[dict]:
    return [t.to_dict() for t in tenants.list()]


@router.get("/tenants/{tenant_id}/route")
async def route_tenant(tenant_id: str) -> dict:
    cluster = federation.route(tenant_id)
    if not cluster:
        raise HTTPException(404, "tenant or cluster not found")
    return cluster.to_dict()


compliance_router = APIRouter(prefix="/compliance", tags=["compliance"])


@compliance_router.get("/fedramp")
async def fedramp_state() -> dict:
    controls = fedramp.list()
    return {
        "summary": fedramp.summary(),
        "controls": [
            {
                "id": c.id,
                "name": c.name,
                "family": c.family,
                "status": c.status,
                "evidence": c.evidence,
                "last_checked": c.last_checked.isoformat(),
            }
            for c in controls
        ],
    }


router.include_router(compliance_router)
