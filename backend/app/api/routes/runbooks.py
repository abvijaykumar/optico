"""Runbook + KEDB endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.data.store import data_store
from app.mcp.base import tool_vault
from app.models.schemas import KEDBEntry, Runbook

router = APIRouter(prefix="/runbooks", tags=["runbooks"])


@router.get("", response_model=list[dict[str, Any]])
async def list_runbooks() -> list[dict[str, Any]]:
    tv_result = await tool_vault.call("mcp-runbook.search_runbook", {})
    return tv_result.data if tv_result.ok else []


@router.post("", response_model=Runbook)
async def upsert(rb: Runbook) -> Runbook:
    return data_store.upsert_runbook(rb)


kedb_router = APIRouter(prefix="/kedb", tags=["kedb"])


@kedb_router.get("", response_model=list[dict[str, Any]])
async def list_kedb(query: str | None = None) -> list[dict[str, Any]]:
    q = query or ""
    result = await tool_vault.call("mcp-itsm.search_kedb", {"query": q})
    return result.data if result.ok else []


@kedb_router.post("", response_model=KEDBEntry)
async def upsert_kedb(entry: KEDBEntry) -> KEDBEntry:
    return data_store.upsert_kedb(entry)


router.include_router(kedb_router)
