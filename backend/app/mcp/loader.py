"""Register all MCP servers with the tool vault."""
from app.mcp.analytics import AnalyticsMCP
from app.mcp.base import tool_vault
from app.mcp.cicd import CICDMCP
from app.mcp.comms import CommsMCP
from app.mcp.itsm import ITSMMCP
from app.mcp.k8s import K8sMCP
from app.mcp.knowledge import KnowledgeMCP
from app.mcp.observability import ObservabilityMCP
from app.mcp.runbook import RunbookMCP


def register_all_servers() -> None:
    for cls in (
        ObservabilityMCP,
        ITSMMCP,
        CommsMCP,
        RunbookMCP,
        CICDMCP,
        KnowledgeMCP,
        K8sMCP,
        AnalyticsMCP,
    ):
        tool_vault.register_server(cls())
