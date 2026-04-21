"""FastAPI entrypoint for the Optico Agentic ITOps Platform."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.agents.registry import register_all_agents
from app.api import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.kg.neo4j_client import kg
from app.mcp import register_all_servers


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    log = get_logger("optico")
    log.info("optico.startup", env=settings.environment, version=__version__)
    register_all_servers()
    register_all_agents()
    await kg.connect()
    yield
    await kg.close()
    log.info("optico.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    async def health():
        return {
            "status": "ok",
            "service": settings.app_name,
            "env": settings.environment,
            "version": __version__,
        }

    return app


app = create_app()
