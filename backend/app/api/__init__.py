from fastapi import APIRouter
from app.api.routes_health import router as health_router
from app.api.routes_reports import router as reports_router
from app.api.routes_matches import router as matches_router
from app.api.routes_contact import router as contact_router
from app.api.routes_auth import router as auth_router
from app.api.routes_communities import router as communities_router
from app.api.routes_admin import router as admin_router
from app.api.routes_analytics import router as analytics_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(communities_router)
api_router.include_router(reports_router)
api_router.include_router(matches_router)
api_router.include_router(contact_router)
api_router.include_router(admin_router)
api_router.include_router(analytics_router)

__all__ = ["api_router"]
