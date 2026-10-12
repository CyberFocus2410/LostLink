"""
Pydantic schemas for Report models with strict validation.
"""
from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict


class ReportType(str, Enum):
    LOST = "LOST"
    FOUND = "FOUND"


class ReportStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    HIDDEN = "HIDDEN"


class CategoryEnum(str, Enum):
    ELECTRONICS = "ELECTRONICS"
    KEYS_CARDS = "KEYS_CARDS"
    BAGS_WALLETS = "BAGS_WALLETS"
    CLOTHING = "CLOTHING"
    DOCUMENTS_BOOKS = "DOCUMENTS_BOOKS"
    JEWELRY_WATCHES = "JEWELRY_WATCHES"
    OTHER = "OTHER"


class ReportCreate(BaseModel):
    type: ReportType
    item_name: str = Field(..., min_length=2, max_length=100)
    category: CategoryEnum
    description: str = Field(..., min_length=5, max_length=1000)
    event_date: date
    location_text: str = Field(..., min_length=2, max_length=150)
    contact_name: str = Field(..., min_length=2, max_length=100)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=30)

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, v: date) -> date:
        # Event date cannot be more than 1 day in the future
        today = date.today()
        if (v - today).days > 1:
            raise ValueError("Event date cannot be in the future")
        return v

    @field_validator("item_name", "location_text", "contact_name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty or only whitespace")
        return s


class ReportUpdate(BaseModel):
    item_name: Optional[str] = Field(None, min_length=2, max_length=100)
    category: Optional[CategoryEnum] = None
    description: Optional[str] = Field(None, min_length=5, max_length=1000)
    event_date: Optional[date] = None
    location_text: Optional[str] = Field(None, min_length=2, max_length=150)
    status: Optional[ReportStatus] = None

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, v: Optional[date]) -> Optional[date]:
        if v is not None:
            today = date.today()
            if (v - today).days > 1:
                raise ValueError("Event date cannot be in the future")
        return v


class ReportOut(BaseModel):
    """Public safe representation of a report. Omits private contact info."""
    id: str
    type: ReportType
    item_name: str
    category: CategoryEnum
    description: str
    event_date: date
    location_text: str
    normalized_location: str
    status: ReportStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportOwnerOut(ReportOut):
    """Detailed view for owner / manager that includes contact information."""
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

