"""
Pydantic schemas for Contact Requests and Moderation Flags.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class ContactRequestCreate(BaseModel):
    report_id: str
    requester_name: str = Field(..., min_length=2, max_length=100)
    requester_email: EmailStr
    requester_phone: Optional[str] = Field(None, max_length=30)
    message: str = Field(..., min_length=10, max_length=1000)


class ContactRequestOut(BaseModel):
    id: str
    report_id: str
    requester_id: Optional[str] = None
    requester_name: str
    message: str
    status: str
    # Private requester contact information (revealed to owner ONLY upon acceptance)
    requester_email: Optional[str] = None
    requester_phone: Optional[str] = None
    owner_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContactRequestAction(BaseModel):
    owner_notes: Optional[str] = Field(None, max_length=500)


class ReportFlagCreate(BaseModel):
    reason: str = Field(..., min_length=5, max_length=255)


class ReportFlagOut(BaseModel):
    id: str
    report_id: str
    reporter_id: Optional[str] = None
    reason: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


