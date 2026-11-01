"""
Contact request workflow with double-blind privacy protection.
Rules:
1. Contact details (email/phone) are never revealed on public report or match cards.
2. Incoming requests are visible only to the report owner.
3. Requester contact details remain masked until the owner explicitly accepts.
4. When accepted, both parties' contact info is safely exchanged via background notifications.
5. If declined, contact details are permanently withheld.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.report import Report, ContactRequest, User
from app.schemas.common import APIResponse
from app.schemas.contact import ContactRequestCreate, ContactRequestOut, ContactRequestAction
from app.services.report_service import ReportService
from app.services.auth_service import get_current_user
from app.services.email_service import EmailService

router = APIRouter(prefix="/contact-requests", tags=["Contact"])


def mask_email(email: str) -> str:
    if "@" not in email:
        return "[Protected]"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: Optional[str]) -> Optional[str]:
    if not phone or len(phone) < 4:
        return "[Protected]"
    return f"***-***-{phone[-4:]}"


def serialize_contact_request(req: ContactRequest, is_owner: bool) -> ContactRequestOut:
    is_revealed = is_owner and req.status == "ACCEPTED"
    return ContactRequestOut(
        id=req.id,
        report_id=req.report_id,
        requester_id=req.requester_id,
        requester_name=req.requester_name,
        message=req.message,
        status=req.status,
        requester_email=req.requester_email if is_revealed else mask_email(req.requester_email),
        requester_phone=req.requester_phone if is_revealed else (mask_phone(req.requester_phone) if req.requester_phone else None),
        owner_response=req.owner_response,
        responded_at=req.responded_at,
        created_at=req.created_at,
    )


@router.post("", response_model=APIResponse[ContactRequestOut], status_code=status.HTTP_201_CREATED)
def create_contact_request(
    request_in: ContactRequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Submits a double-blind contact request. Triggers background notification to report owner."""
    report = ReportService.get_report(db, request_in.report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{request_in.report_id}' was not found.",
        )

    contact_req = ContactRequest(
        report_id=report.id,
        requester_id=current_user.id if current_user else None,
        requester_name=request_in.requester_name.strip(),
        requester_email=request_in.requester_email.lower().strip(),
        requester_phone=request_in.requester_phone.strip() if request_in.requester_phone else None,
        message=request_in.message.strip(),
        status="PENDING",
    )
    db.add(contact_req)
    db.commit()
    db.refresh(contact_req)

    # Background email notification to report owner
    target_owner_email = report.contact_email
    target_owner_name = report.contact_name
    background_tasks.add_task(
        EmailService.send_contact_request_notification,
        owner_email=target_owner_email,
        owner_name=target_owner_name,
        item_name=report.item_name,
        requester_name=contact_req.requester_name,
        message=contact_req.message,
    )

    out = serialize_contact_request(contact_req, is_owner=False)
    return APIResponse.success(data=out)


@router.get("/received", response_model=APIResponse[List[ContactRequestOut]])
def list_received_contact_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists all contact requests received for reports owned by the authenticated user."""
    user_report_ids = [
        r.id for r in db.query(Report.id).filter(Report.owner_id == current_user.id).all()
    ]
    if not user_report_ids:
        return APIResponse.success(data=[])

    requests = (
        db.query(ContactRequest)
        .filter(ContactRequest.report_id.in_(user_report_ids))
        .order_by(ContactRequest.created_at.desc())
        .all()
    )

    out_list = [serialize_contact_request(req, is_owner=True) for req in requests]
    return APIResponse.success(data=out_list)


@router.get("/sent", response_model=APIResponse[List[ContactRequestOut]])
def list_sent_contact_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists all contact requests sent by the authenticated user."""
    requests = (
        db.query(ContactRequest)
        .filter(ContactRequest.requester_id == current_user.id)
        .order_by(ContactRequest.created_at.desc())
        .all()
    )
    out_list = [
        ContactRequestOut(
            id=req.id,
            report_id=req.report_id,
            requester_id=req.requester_id,
            requester_name=req.requester_name,
            message=req.message,
            status=req.status,
            requester_email=req.requester_email,
            requester_phone=req.requester_phone,
            owner_response=req.owner_response,
            responded_at=req.responded_at,
            created_at=req.created_at,
        )
        for req in requests
    ]
    return APIResponse.success(data=out_list)


@router.post("/{request_id}/accept", response_model=APIResponse[ContactRequestOut])
def accept_contact_request(
    request_id: str,
    action: ContactRequestAction,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Owner accepts a contact request, unmasking contact information and emailing the requester."""
    req = db.query(ContactRequest).filter(ContactRequest.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact request '{request_id}' not found.",
        )

    report = db.query(Report).filter(Report.id == req.report_id).first()
    if not report or (report.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to accept this contact request.",
        )

    req.status = "ACCEPTED"
    req.owner_response = action.owner_notes.strip() if action.owner_notes else None
    req.responded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)

    background_tasks.add_task(
        EmailService.send_contact_accepted_notification,
        requester_email=req.requester_email,
        requester_name=req.requester_name,
        item_name=report.item_name,
        owner_name=report.contact_name,
        owner_email=report.contact_email,
        owner_phone=report.contact_phone,
        owner_notes=req.owner_response,
    )

    out = serialize_contact_request(req, is_owner=True)
    return APIResponse.success(data=out)


@router.post("/{request_id}/decline", response_model=APIResponse[ContactRequestOut])
def decline_contact_request(
    request_id: str,
    action: ContactRequestAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Owner declines a contact request. Contact info remains permanently hidden."""
    req = db.query(ContactRequest).filter(ContactRequest.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact request '{request_id}' not found.",
        )

    report = db.query(Report).filter(Report.id == req.report_id).first()
    if not report or (report.owner_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to decline this contact request.",
        )

    req.status = "DECLINED"
    req.owner_response = action.owner_notes.strip() if action.owner_notes else None
    req.responded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)

    out = serialize_contact_request(req, is_owner=True)
    return APIResponse.success(data=out)
