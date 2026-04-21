"""Knowledge graph read endpoints — used by dashboards + agents."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.kg.neo4j_client import kg

router = APIRouter(prefix="/kg", tags=["kg"])


@router.get("/services")
async def list_services() -> list[dict[str, Any]]:
    return await kg.all_services()


@router.get("/services/{name}/context")
async def service_context(name: str) -> dict[str, Any]:
    return await kg.service_context(name)
