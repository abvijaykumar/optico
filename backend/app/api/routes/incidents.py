"""Incident CRUD + status updates."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.data.store import data_store
from app.kg.neo4j_client import kg
from app.models.schemas import Incident, IncidentStatus

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[Incident])
async def list_incidents(status: IncidentStatus | None = None) -> list[Incident]:
    return data_store.list_incidents(status=status)


@router.post("", response_model=Incident)
async def create_incident(incident: Incident) -> Incident:
    saved = data_store.upsert_incident(incident)
    await kg.add_incident_node(saved.model_dump(mode="json"))
    return saved


@router.get("/{incident_id}", response_model=Incident)
async def get_incident(incident_id: UUID) -> Incident:
    inc = data_store.get_incident(incident_id)
    if not inc:
        raise HTTPException(404, "incident not found")
    return inc


@router.patch("/{incident_id}", response_model=Incident)
async def update_incident(incident_id: UUID, patch: dict) -> Incident:
    inc = data_store.get_incident(incident_id)
    if not inc:
        raise HTTPException(404, "incident not found")
    for k, v in patch.items():
        if hasattr(inc, k):
            setattr(inc, k, v)
    data_store.upsert_incident(inc)
    return inc
