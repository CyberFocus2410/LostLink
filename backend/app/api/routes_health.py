"""
Health check and service diagnostics endpoint.
Confirms database connectivity, engine dialect, and in-memory index size.
"""
import logging
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db, engine
from app.schemas.common import APIResponse, APIMeta
from app.matching.index import matching_index
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=APIResponse[dict])
def health_check(response: Response, db: Session = Depends(get_db)):
    db_status = "connected"
    db_dialect = db.bind.dialect.name if hasattr(db, "bind") and db.bind else engine.dialect.name
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    stats = matching_index.get_stats()
    data = {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "service": settings.APP_NAME,
        "environment": settings.ENV,
        "database": {
            "status": db_status,
            "dialect": db_dialect,
        },
        "indexed_active_reports": stats["indexed_active_reports"],
        "indexed_categories": stats["indexed_categories"],
        "indexed_tokens": stats["indexed_tokens"],
        "approx_memory_bytes": stats["approx_memory_bytes"],
    }
    return APIResponse.success(data=data, meta=APIMeta(extra={"version": "1.0.0"}))
