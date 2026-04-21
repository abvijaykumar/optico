"""LLM selection helper.

Chooses a LangChain chat model based on available API keys. If neither
provider is configured we return a deterministic `FakeListChatModel`
backed by crafted responses so the full LangGraph executes in tests and
demos without any external dependency.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


_FAKE_RESPONSES = [
    "Detected a correlated spike in checkout 5xx and orders-api latency. "
    "The most recent change (rel-2026.04.21-001) is the prime suspect. "
    "Recommend rollback and incident creation.",
    "Three candidate root causes, ranked: (1) env var drift from the "
    "latest deploy (0.78); (2) orders-db connection pool exhaustion "
    "(0.14); (3) upstream payment provider throttling (0.08).",
    "PIR draft generated: timeline from 12:05 UTC deploy → 12:30 first "
    "alert → 12:42 rollback → 12:55 resolution. Five-whys and three "
    "action items proposed.",
    "Release risk score 0.24 — low. Recent service-area stability good; "
    "no freeze window conflict. Auto-approval recommended.",
]


@lru_cache(maxsize=1)
def get_llm(model_override: str | None = None) -> BaseChatModel:
    settings = get_settings()

    if settings.anthropic_api_key:
        from langchain_anthropic import ChatAnthropic

        log.info("llm.init", provider="anthropic", model=settings.default_model)
        return ChatAnthropic(
            model=model_override or settings.default_model,
            temperature=0.0,
            max_tokens=1024,
            api_key=settings.anthropic_api_key,
        )

    if settings.openai_api_key:
        from langchain_openai import ChatOpenAI

        log.info("llm.init", provider="openai", model="gpt-4o")
        return ChatOpenAI(model="gpt-4o", temperature=0.0, api_key=settings.openai_api_key)

    log.warning("llm.init", provider="fake", reason="no_api_key_configured")
    return FakeListChatModel(responses=_FAKE_RESPONSES)


def ainvoke_text(prompt: str, *, model: str | None = None, **kwargs: Any) -> str:
    """Convenience: return just the string content of a chat response."""
    llm = get_llm(model)
    result = llm.invoke(prompt, **kwargs)
    return getattr(result, "content", str(result))
