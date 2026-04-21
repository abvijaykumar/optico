"""Register all MCP servers with the tool vault."""
from app.mcp.analytics import AnalyticsMCP
from app.mcp.aws import AWSMCP
from app.mcp.azure import AzureMCP
from app.mcp.base import tool_vault
from app.mcp.cicd import CICDMCP
from app.mcp.comms import CommsMCP
from app.mcp.db import DBMCP
from app.mcp.finops import FinOpsMCP
from app.mcp.flags import FlagsMCP
from app.mcp.gcp import GCPMCP
from app.mcp.gitops import GitOpsMCP
from app.mcp.hardware import HardwareMCP
from app.mcp.iac import IaCMCP
from app.mcp.itsm import ITSMMCP
from app.mcp.k8s import K8sMCP
from app.mcp.knowledge import KnowledgeMCP
from app.mcp.messaging import MessagingMCP
from app.mcp.network import NetworkMCP
from app.mcp.observability import ObservabilityMCP
from app.mcp.runbook import RunbookMCP
from app.mcp.security import SecurityMCP


def register_all_servers() -> None:
    """Instantiate and register every MCP server with the vault."""
    for cls in (
        # Phase 1
        ObservabilityMCP,
        ITSMMCP,
        CommsMCP,
        RunbookMCP,
        KnowledgeMCP,
        # Phase 2
        CICDMCP,
        GitOpsMCP,
        FlagsMCP,
        IaCMCP,
        # Phase 3 — cloud
        AWSMCP,
        AzureMCP,
        GCPMCP,
        # Phase 3 — infra / stack
        K8sMCP,
        DBMCP,
        MessagingMCP,
        HardwareMCP,
        NetworkMCP,
        # Phase 4 — security, analytics, finops
        SecurityMCP,
        AnalyticsMCP,
        FinOpsMCP,
    ):
        tool_vault.register_server(cls())
