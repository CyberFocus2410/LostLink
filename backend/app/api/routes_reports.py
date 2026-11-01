"""
Reports API endpoints for LostLink.
Full lifecycle: creation, filtering, detail, updates, resolution, and flagging.
"""
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, HTTPException, File, UploadFile
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
    ReportImageOut,
)
from app.schemas.contact import ReportFlagCreate, ReportFlagOut
from app.services.report_service import ReportService
from app.services.auth_service import get_current_user, get_optional_current_user
from app.services.image_service import ImageValidationError

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
    owner_id: Optional[str] = Query(None, description="Filter by owner ID"),
    community_id: Optional[str] = Query(None, description="Filter by community ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: str = Query("date_desc", description="Sort order: date_desc, date_asc, created_desc, created_asc"),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
):
    req_status = status_filter.value if status_filter else None
    if req_status == "HIDDEN" and getattr(current_user, "role", "user") not in ("admin", "moderator"):
        req_status = "ACTIVE"

    items, total = ReportService.list_reports(
        db,
        q=q,
        report_type=type.value if type else None,
        category=category.value if category else None,
        status=req_status,
        date_from=date_from,
        date_to=date_to,
        location=location,
        owner_id=owner_id,
        community_id=community_id,
        page=page,
        limit=limit,
        sort=sort,
    )

    out_items = [ReportOut.model_validate(r) for r in items]
    meta = APIMeta(page=page, limit=limit, total=total)
    return APIResponse.success(data=out_items, meta=meta)


@router.get("/mine", response_model=APIResponse[List[ReportOut]])
def list_my_reports(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Returns reports created by the currently authenticated user."""
    items, total = ReportService.list_reports(
        db,
        owner_id=current_user.id,
        page=page,
        limit=limit,
        sort="created_desc",
    )
    out_items = [ReportOut.model_validate(r) for r in items]
    meta = APIMeta(page=page, limit=limit, total=total)
    return APIResponse.success(data=out_items, meta=meta)


@router.post("", response_model=APIResponse[ReportOut], status_code=status.HTTP_201_CREATED)
def create_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    created = ReportService.create_report(db, report_in, owner_id=current_user.id)
    out = ReportOut.model_validate(created)
    return APIResponse.success(data=out)


@router.get("/{report_id}", response_model=APIResponse[ReportOut])
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
):
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found.",
        )
    if report.status == "HIDDEN":
        user_role = getattr(current_user, "role", "user")
        user_id = getattr(current_user, "id", None)
        if user_role not in ("admin", "moderator") and user_id != report.owner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This report has been taken down by moderators.",
            )
    return APIResponse.success(data=ReportOut.model_validate(report))


@router.patch("/{report_id}", response_model=APIResponse[ReportOut])
def update_report(
    report_id: str,
    update_in: ReportUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found.",
        )
    if report.owner_id and report.owner_id != current_user.id and getattr(current_user, "role", "user") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this report.",
        )
    updated = ReportService.update_report(db, report_id, update_in)
    return APIResponse.success(data=ReportOut.model_validate(updated))


@router.post("/{report_id}/resolve", response_model=APIResponse[ReportOut])
def resolve_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found.",
        )
    if report.owner_id and report.owner_id != current_user.id and getattr(current_user, "role", "user") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to resolve this report.",
        )
    resolved = ReportService.resolve_report(db, report_id)
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


@router.post("/{report_id}/images", response_model=APIResponse[ReportImageOut], status_code=status.HTTP_201_CREATED)
async def upload_report_image(
    report_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Uploads and associates an image with a report (max 3 images, owner only)."""
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found.",
        )
    if report.owner_id and report.owner_id != current_user.id and getattr(current_user, "role", "user") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to upload photos for this report.",
        )
    if len(report.images) >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 3 images allowed per report.",
        )

    raw_bytes = await file.read()
    try:
        image_record = ReportService.add_report_image(
            db,
            report_id=report_id,
            file_bytes=raw_bytes,
            original_filename=file.filename or "image.jpg",
            content_type=file.content_type or "image/jpeg",
        )
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return APIResponse.success(data=ReportImageOut.model_validate(image_record))


@router.delete("/{report_id}/images/{image_id}", response_model=APIResponse[dict])
def delete_report_image(
    report_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Deletes an image from a report (owner only)."""
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found.",
        )
    if report.owner_id and report.owner_id != current_user.id and getattr(current_user, "role", "user") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete photos from this report.",
        )

    deleted = ReportService.delete_report_image(db, report_id=report_id, image_id=image_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID '{image_id}' not found on report '{report_id}'.",
        )

    return APIResponse.success(data={"message": "Image deleted successfully", "image_id": image_id})

