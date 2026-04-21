from fastapi import APIRouter

from app.api.routes import (
    agents,
    changes,
    dashboards,
    federation,
    governance,
    hitl,
    incidents,
    kg,
    mcp,
    runbooks,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(agents.router)
api_router.include_router(incidents.router)
api_router.include_router(changes.router)
api_router.include_router(hitl.router)
api_router.include_router(mcp.router)
api_router.include_router(kg.router)
api_router.include_router(runbooks.router)
api_router.include_router(dashboards.router)
api_router.include_router(governance.router)
api_router.include_router(federation.router)
