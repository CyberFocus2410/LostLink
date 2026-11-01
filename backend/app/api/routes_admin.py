"""
Admin and moderation endpoints for LostLink.
Allows administrators to:
- Review and dismiss reported abuse flags
- Moderate and hide inappropriate reports
- Deactivate malicious or abusive user accounts
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.report import Report, ReportFlag, User
from app.schemas.common import APIResponse
from app.schemas.contact import ReportFlagOut
from app.schemas.report import ReportOut
from app.schemas.auth import UserOut
from app.services.auth_service import get_current_user
from app.services.report_service import ReportService

router = APIRouter(prefix="/admin", tags=["Admin & Moderation"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("admin", "moderator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required.",
        )
    return current_user


class FlagReviewPayload(BaseModel):
    action: str = Field(..., pattern="^(DISMISSED|REVIEWED)$")


class ReportStatusPayload(BaseModel):
    status: str = Field(..., pattern="^(ACTIVE|RESOLVED|HIDDEN)$")


class UserStatusPayload(BaseModel):
    is_active: bool


@router.get("/flags", response_model=APIResponse[List[ReportFlagOut]])
def list_reported_flags(
    flag_status: Optional[str] = "OPEN",
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Lists abuse flags for review with full item and photo details."""
    query = db.query(ReportFlag)
    if flag_status:
        query = query.filter(ReportFlag.status == flag_status)
    flags = query.order_by(ReportFlag.created_at.desc()).all()
    
    out = []
    for f in flags:
        rep = db.query(Report).filter(Report.id == f.report_id).first()
        first_img = rep.images[0].image_url if (rep and rep.images) else None
        out.append(
            ReportFlagOut(
                id=f.id,
                report_id=f.report_id,
                reporter_id=f.reporter_id,
                reason=f.reason,
                status=f.status,
                created_at=f.created_at,
                report_item_name=rep.item_name if rep else "Deleted Report",
                report_type=rep.type if rep else "UNKNOWN",
                report_category=rep.category if rep else "OTHER",
                report_status=rep.status if rep else "DELETED",
                report_description=rep.description if rep else "",
                report_location=rep.location_text if rep else "",
                report_image_url=first_img,
            )
        )
    return APIResponse.success(data=out)


@router.post("/flags/{flag_id}/review", response_model=APIResponse[ReportFlagOut])
def review_flag(
    flag_id: str,
    payload: FlagReviewPayload,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Marks a report flag as reviewed or dismissed."""
    flag = db.query(ReportFlag).filter(ReportFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found.")

    flag.status = payload.action
    flag.reviewed_by = admin.id
    flag.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(flag)
    return APIResponse.success(data=ReportFlagOut.model_validate(flag))


@router.patch("/reports/{report_id}/status", response_model=APIResponse[ReportOut])
def moderate_report_status(
    report_id: str,
    payload: ReportStatusPayload,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Moderates a report by altering its status (e.g. setting to HIDDEN to take down an abusive post)."""
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    report.status = payload.status
    db.commit()
    db.refresh(report)

    # Refresh in-memory index
    from app.matching.index import ReportRecord, matching_index
    if payload.status == "ACTIVE":
        matching_index.add(ReportRecord.from_model(report))
    else:
        matching_index.remove(report.id)

    return APIResponse.success(data=ReportOut.model_validate(report))


@router.patch("/users/{user_id}/status", response_model=APIResponse[dict])
def moderate_user_status(
    user_id: str,
    payload: UserStatusPayload,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Activates or deactivates a user account."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    target_user.is_active = payload.is_active
    db.commit()
    return APIResponse.success(data={
        "user_id": target_user.id,
        "is_active": target_user.is_active,
        "message": f"User account has been {'activated' if payload.is_active else 'deactivated'}."
    })


@router.get("/reports", response_model=APIResponse[List[ReportOut]])
def list_admin_reports(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Lists all reports for admin moderation, including HIDDEN and RESOLVED."""
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status)
    reports = query.order_by(Report.created_at.desc()).limit(limit).all()
    out = [ReportOut.model_validate(r) for r in reports]
    return APIResponse.success(data=out)


@router.get("/users", response_model=APIResponse[List[UserOut]])
def list_admin_users(
    search: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Lists users for account moderation."""
    query = db.query(User)
    if search:
        s = f"%{search.strip().lower()}%"
        query = query.filter((User.email.ilike(s)) | (User.display_name.ilike(s)))
    users = query.order_by(User.created_at.desc()).limit(limit).all()
    out = [UserOut.model_validate(u) for u in users]
    return APIResponse.success(data=out)

