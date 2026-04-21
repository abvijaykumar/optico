"""Tool Vault inspection + direct call (admin / debug)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.mcp.base import tool_vault

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/servers")
async def list_servers() -> list[dict[str, Any]]:
    out = []
    for s in tool_vault.list_servers():
        out.append(
            {
                "name": s.name,
                "description": s.description,
                "tools": [
                    {
                        "name": t.name,
                        "qualified_name": t.qualified_name,
                        "description": t.description,
                        "read_only": t.read_only,
                        "min_autonomy": int(t.min_autonomy),
                        "args_schema": t.args_schema,
                    }
                    for t in s.tools()
                ],
            }
        )
    return out


@router.post("/call")
async def call_tool(body: dict[str, Any]) -> dict[str, Any]:
    tool = body.get("tool")
    args = body.get("args", {})
    if not tool:
        raise HTTPException(400, "tool is required")
    result = await tool_vault.call(tool, args)
    return result.model_dump(mode="json")
