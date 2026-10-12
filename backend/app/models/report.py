"""
SQLAlchemy database models for LostLink.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    type = Column(String(10), nullable=False, index=True)  # LOST or FOUND
    item_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    event_date = Column(Date, nullable=False, index=True)
    location_text = Column(String(150), nullable=False)
    normalized_location = Column(String(150), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)  # ACTIVE, RESOLVED, HIDDEN

    # Private contact details (never exposed in public lists or match payloads)
    contact_name = Column(String(100), nullable=False)
    contact_email = Column(String(120), nullable=False)
    contact_phone = Column(String(30), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    contact_requests = relationship("ContactRequest", back_populates="report", cascade="all, delete-orphan")
    flags = relationship("ReportFlag", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_reports_type_status", "type", "status"),
        Index("ix_reports_category_status", "category", "status"),
    )


class ContactRequest(Base):
    __tablename__ = "contact_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    requester_name = Column(String(100), nullable=False)
    requester_email = Column(String(120), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING, ACKNOWLEDGED, RESOLVED
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    report = relationship("Report", back_populates="contact_requests")


class ReportFlag(Base):
    __tablename__ = "report_flags"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    report = relationship("Report", back_populates="flags")
