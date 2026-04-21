"""Tool Vault base classes.

Every MCP server declares a set of tools with typed args, an auth policy,
an autonomy tag, and a blast-radius hint. The vault surfaces them to
agents via a single, governed interface.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Protocol

from pydantic import BaseModel

from app.core.logging import get_logger
from app.models.schemas import AutonomyLevel

log = get_logger(__name__)


class ToolHandler(Protocol):
    async def __call__(self, **kwargs: Any) -> Any: ...


@dataclass
class MCPTool:
    name: str                     # "query_metrics"
    server: str                   # "mcp-observability"
    description: str
    args_schema: dict[str, Any]   # JSONSchema-ish
    handler: Callable[..., Awaitable[Any]]
    read_only: bool = False
    min_autonomy: AutonomyLevel = AutonomyLevel.L0_RECOMMEND
    blast_radius: dict[str, Any] = field(default_factory=dict)

    @property
    def qualified_name(self) -> str:
        return f"{self.server}.{self.name}"


class ToolResult(BaseModel):
    tool: str
    ok: bool
    data: Any | None = None
    error: str | None = None
    duration_ms: int = 0
    ran_at: datetime = datetime.now(timezone.utc)  # overridden on each call


class MCPServer:
    """Base class for MCP servers.

    Subclass, set `name`, and decorate async methods with `@tool(...)`.
    """

    name: str = "mcp-base"
    description: str = ""

    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}
        self._discover()

    # -- discovery ---------------------------------------------------------

    def _discover(self) -> None:
        for attr_name in dir(self):
            attr = getattr(self, attr_name, None)
            decl = getattr(attr, "__mcp_tool__", None)
            if not decl:
                continue
            tool = MCPTool(
                name=decl["name"],
                server=self.name,
                description=decl["description"],
                args_schema=decl.get("args_schema", {}),
                handler=attr,
                read_only=decl.get("read_only", False),
                min_autonomy=decl.get("min_autonomy", AutonomyLevel.L0_RECOMMEND),
                blast_radius=decl.get("blast_radius", {}),
            )
            self._tools[tool.name] = tool

    def tools(self) -> list[MCPTool]:
        return list(self._tools.values())


# -- decorator used on MCPServer methods -------------------------------------


def tool(
    *,
    name: str,
    description: str,
    args_schema: dict[str, Any] | None = None,
    read_only: bool = False,
    min_autonomy: AutonomyLevel = AutonomyLevel.L0_RECOMMEND,
    blast_radius: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    def decorate(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        if not inspect.iscoroutinefunction(fn):
            raise TypeError(f"Tool {name} must be an async function")
        fn.__mcp_tool__ = {  # type: ignore[attr-defined]
            "name": name,
            "description": description,
            "args_schema": args_schema or {},
            "read_only": read_only,
            "min_autonomy": min_autonomy,
            "blast_radius": blast_radius or {},
        }
        return fn

    return decorate


# -- the vault ----------------------------------------------------------------


class ToolVault:
    """Central registry of MCP servers and their tools."""

    def __init__(self) -> None:
        self._servers: dict[str, MCPServer] = {}
        self._tools: dict[str, MCPTool] = {}

    def register_server(self, server: MCPServer) -> None:
        self._servers[server.name] = server
        for t in server.tools():
            self._tools[t.qualified_name] = t
        log.info(
            "mcp.registered",
            server=server.name,
            tools=[t.name for t in server.tools()],
        )

    def get(self, qualified_name: str) -> MCPTool | None:
        return self._tools.get(qualified_name)

    def list_tools(self, server: str | None = None) -> list[MCPTool]:
        if server:
            return [t for t in self._tools.values() if t.server == server]
        return list(self._tools.values())

    def list_servers(self) -> list[MCPServer]:
        return list(self._servers.values())

    async def call(
        self,
        qualified_name: str,
        args: dict[str, Any],
    ) -> ToolResult:
        tool_ = self.get(qualified_name)
        if not tool_:
            return ToolResult(
                tool=qualified_name, ok=False, error="tool_not_found"
            )
        start = datetime.now(timezone.utc)
        try:
            data = await tool_.handler(**args)
            duration = int(
                (datetime.now(timezone.utc) - start).total_seconds() * 1000
            )
            return ToolResult(
                tool=qualified_name, ok=True, data=data, duration_ms=duration
            )
        except Exception as exc:  # pragma: no cover — surfaced to caller
            log.exception("mcp.call_failed", tool=qualified_name)
            return ToolResult(
                tool=qualified_name, ok=False, error=str(exc)
            )


tool_vault = ToolVault()
