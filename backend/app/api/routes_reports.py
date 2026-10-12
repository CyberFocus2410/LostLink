"""
Reports API endpoints for LostLink.
Full lifecycle: creation, filtering, detail, updates, resolution, and flagging.
"""
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.common import APIResponse, APIMeta, APIError
from app.schemas.report import (
    ReportType,
    ReportStatus,
    CategoryEnum,
    ReportCreate,
    ReportUpdate,
    ReportOut,
)
from app.schemas.contact import ReportFlagCreate, ReportFlagOut
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=APIResponse[List[ReportOut]])
def list_reports(
    q: Optional[str] = Query(None, description="Search keyword in title, description, or location"),
    type: Optional[ReportType] = Query(None, description="LOST or FOUND"),
    category: Optional[CategoryEnum] = Query(None, description="Item category"),
    status_filter: Optional[ReportStatus] = Query(None, alias="status", description="ACTIVE, RESOLVED, HIDDEN"),
    date_from: Optional[date] = Query(None, description="Earliest event date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Latest event date (YYYY-MM-DD)"),
    location: Optional[str] = Query(None, description="Location substring"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: str = Query("date_desc", description="Sort order: date_desc, date_asc, created_desc, created_asc"),
    db: Session = Depends(get_db),
):
    items, total = ReportService.list_reports(
        db,
        q=q,
        report_type=type.value if type else None,
        category=category.value if category else None,
        status=status_filter.value if status_filter else None,
        date_from=date_from,
        date_to=date_to,
        location=location,
        page=page,
        limit=limit,
        sort=sort,
    )

    out_items = [ReportOut.model_validate(r) for r in items]
    meta = APIMeta(page=page, limit=limit, total=total)
    return APIResponse.success(data=out_items, meta=meta)


@router.post("", response_model=APIResponse[ReportOut], status_code=status.HTTP_201_CREATED)
def create_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
):
    created = ReportService.create_report(db, report_in)
    out = ReportOut.model_validate(created)
    return APIResponse.success(data=out)


@router.get("/{report_id}", response_model=APIResponse[ReportOut])
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found.",
        )
    return APIResponse.success(data=ReportOut.model_validate(report))


@router.patch("/{report_id}", response_model=APIResponse[ReportOut])
def update_report(
    report_id: str,
    update_in: ReportUpdate,
    db: Session = Depends(get_db),
):
    updated = ReportService.update_report(db, report_id, update_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found.",
        )
    return APIResponse.success(data=ReportOut.model_validate(updated))


@router.post("/{report_id}/resolve", response_model=APIResponse[ReportOut])
def resolve_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    resolved = ReportService.resolve_report(db, report_id)
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found.",
        )
    return APIResponse.success(data=ReportOut.model_validate(resolved))


@router.post("/{report_id}/flag", response_model=APIResponse[ReportFlagOut], status_code=status.HTTP_201_CREATED)
def flag_report(
    report_id: str,
    flag_in: ReportFlagCreate,
    db: Session = Depends(get_db),
):
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found.",
        )
    flag = ReportService.flag_report(db, report_id, flag_in)
    return APIResponse.success(data=ReportFlagOut.model_validate(flag))
