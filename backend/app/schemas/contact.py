"""
Pydantic schemas for Contact Requests and Moderation Flags.
"""
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class ContactRequestCreate(BaseModel):
    report_id: str
    requester_name: str = Field(..., min_length=2, max_length=100)
    requester_email: EmailStr
    message: str = Field(..., min_length=10, max_length=1000)


class ContactRequestOut(BaseModel):
    id: str
    report_id: str
    requester_name: str
    status: str
    created_at: datetime
    # Note: requester_email and full message are kept private / handled safely

    model_config = ConfigDict(from_attributes=True)


class ReportFlagCreate(BaseModel):
    reason: str = Field(..., min_length=5, max_length=255)


class ReportFlagOut(BaseModel):
    id: str
    report_id: str
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

