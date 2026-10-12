from fastapi import APIRouter
from app.api.routes_health import router as health_router
from app.api.routes_reports import router as reports_router
from app.api.routes_matches import router as matches_router
from app.api.routes_contact import router as contact_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(reports_router)
api_router.include_router(matches_router)
api_router.include_router(contact_router)

__all__ = ["api_router"]
