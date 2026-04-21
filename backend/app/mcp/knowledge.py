"""mcp-knowledge — Confluence / SharePoint / articles."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.mcp.base import MCPServer, tool


class KnowledgeMCP(MCPServer):
    name = "mcp-knowledge"
    description = "Search institutional knowledge; upsert articles."

    _ARTICLES: list[dict[str, Any]] = [
        {
            "id": "KB-checkout-arch",
            "title": "Checkout architecture overview",
            "body": "Checkout routes through API gateway → checkout-svc → orders-api → orders-db.",
            "tags": ["architecture", "checkout"],
        },
        {
            "id": "KB-incident-playbook",
            "title": "Incident response playbook",
            "body": "Sev1 = CIO paged; war room within 5 min; PIR due in 5 business days.",
            "tags": ["incident", "process"],
        },
    ]

    @tool(
        name="search_confluence",
        description="Search the knowledge base.",
        args_schema={"query": {"type": "string", "required": True}},
        read_only=True,
    )
    async def search_confluence(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        return [
            a
            for a in self._ARTICLES
            if q in a["title"].lower() or q in a["body"].lower()
        ]

    @tool(
        name="search_sharepoint",
        description="Alias for search_confluence (federated KB).",
        args_schema={"query": {"type": "string", "required": True}},
        read_only=True,
    )
    async def search_sharepoint(self, query: str) -> list[dict[str, Any]]:
        return await self.search_confluence(query=query)

    @tool(
        name="upsert_article",
        description="Create or update a knowledge article.",
        args_schema={
            "title": {"type": "string", "required": True},
            "body": {"type": "string", "required": True},
            "tags": {"type": "array"},
            "id": {"type": "string"},
        },
    )
    async def upsert_article(
        self,
        title: str,
        body: str,
        tags: list[str] | None = None,
        id: str | None = None,
    ) -> dict[str, Any]:
        record = {
            "id": id or f"KB-{str(uuid4())[:8]}",
            "title": title,
            "body": body,
            "tags": tags or [],
        }
        self._ARTICLES = [a for a in self._ARTICLES if a["id"] != record["id"]]
        self._ARTICLES.append(record)
        return record
