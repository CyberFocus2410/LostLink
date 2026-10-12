"""
Health check and service diagnostics endpoint.
"""
from fastapi import APIRouter
from app.schemas.common import APIResponse, APIMeta
from app.matching.index import matching_index
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=APIResponse[dict])
def health_check():
    data = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.ENV,
        "indexed_records": len(matching_index.records),
        "indexed_categories": len(matching_index.category_index),
        "indexed_tokens": len(matching_index.keyword_index),
    }
    return APIResponse.success(data=data, meta=APIMeta(extra={"version": "1.0.0"}))
