"""
Contact request endpoint for LostLink.
Allows reporters/finders to initiate contact without leaking private email/phone.
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.common import APIResponse
from app.schemas.contact import ContactRequestCreate, ContactRequestOut
from app.services.report_service import ReportService

router = APIRouter(prefix="/contact-requests", tags=["Contact"])


@router.post("", response_model=APIResponse[ContactRequestOut], status_code=status.HTTP_201_CREATED)
def create_contact_request(
    request_in: ContactRequestCreate,
    db: Session = Depends(get_db),
):
    report = ReportService.get_report(db, request_in.report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{request_in.report_id}' was not found.",
        )

    contact_req = ReportService.create_contact_request(db, request_in)
    out = ContactRequestOut.model_validate(contact_req)
    return APIResponse.success(data=out)
