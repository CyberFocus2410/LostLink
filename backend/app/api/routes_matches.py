"""
Matches API endpoint for LostLink.
Retrieves explainable, ranked candidate matches for a report.
"""
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.common import APIResponse, APIMeta
from app.schemas.match import MatchListOut
from app.services.report_service import ReportService
from app.config import settings

router = APIRouter(prefix="/reports", tags=["Matching"])


@router.get("/{report_id}/matches", response_model=APIResponse[MatchListOut])
def get_report_matches(
    report_id: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of matches to return"),
    minimum_score: float = Query(
        0.0,
        ge=0.0,
        le=100.0,
        description="Minimum score threshold (0-100)",
    ),
    db: Session = Depends(get_db),
):
    source_report = ReportService.get_report(db, report_id)
    if not source_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found.",
        )

    match_result = ReportService.get_matches(
        db,
        report_id=report_id,
        limit=limit,
        min_score=minimum_score,
    )

    if not match_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unable to compute matches for report '{report_id}'.",
        )

    meta = APIMeta(
        limit=limit,
        total=len(match_result.matches),
        extra={
            "candidate_pool_size": match_result.candidate_count,
            "weights": {
                "category": settings.WEIGHT_CATEGORY,
                "location": settings.WEIGHT_LOCATION,
                "date": settings.WEIGHT_DATE,
                "keyword": settings.WEIGHT_KEYWORD,
            },
        },
    )
    return APIResponse.success(data=match_result, meta=meta)
