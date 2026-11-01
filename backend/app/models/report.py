"""
SQLAlchemy database models for LostLink.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, Boolean, Index, Float, Integer
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Community(Base):
    __tablename__ = "communities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    reports = relationship("Report", back_populates="community")
    facility_clusters = relationship("FacilityCluster", back_populates="community", cascade="all, delete-orphan")


class FacilityCluster(Base):
    __tablename__ = "facility_clusters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    community_id = Column(String(36), ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    aliases = Column(Text, nullable=False)  # Comma-separated or JSON list of alias terms
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    community = relationship("Community", back_populates="facility_clusters")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    display_name = Column(String(100), nullable=False)
    email = Column(String(254), nullable=False, unique=True, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(20), nullable=False, default="user")  # user, moderator
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    reports = relationship("Report", back_populates="owner", foreign_keys="Report.owner_id")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    """Server-side refresh token store — only the hash is kept, enabling true revocation."""
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hex
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    user = relationship("User", back_populates="refresh_tokens")


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

    # Nullable: existing seed data has no owner; set for authenticated users
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Community and coordinates
    community_id = Column(String(36), ForeignKey("communities.id", ondelete="SET NULL"), nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Private contact details (never exposed in public lists or match payloads)
    contact_name = Column(String(100), nullable=False)
    contact_email = Column(String(120), nullable=False)
    contact_phone = Column(String(30), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    owner = relationship("User", back_populates="reports", foreign_keys=[owner_id])
    community = relationship("Community", back_populates="reports", foreign_keys=[community_id])
    images = relationship("ReportImage", back_populates="report", cascade="all, delete-orphan", order_by="ReportImage.created_at")
    contact_requests = relationship("ContactRequest", back_populates="report", cascade="all, delete-orphan")
    flags = relationship("ReportFlag", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_reports_type_status", "type", "status"),
        Index("ix_reports_category_status", "category", "status"),
        Index("ix_reports_owner_status", "owner_id", "status"),
        Index("ix_reports_community_status", "community_id", "status"),
        Index("ix_reports_date_status", "event_date", "status"),
    )


class ContactRequest(Base):
    __tablename__ = "contact_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    requester_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    requester_name = Column(String(100), nullable=False)
    requester_email = Column(String(120), nullable=False)
    requester_phone = Column(String(30), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)  # PENDING, ACCEPTED, DECLINED
    owner_response = Column(Text, nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    report = relationship("Report", back_populates="contact_requests")
    requester = relationship("User", foreign_keys=[requester_id])


class ReportFlag(Base):
    __tablename__ = "report_flags"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="OPEN", index=True)  # OPEN, REVIEWED, DISMISSED
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    report = relationship("Report", back_populates="flags")
    reporter = relationship("User", foreign_keys=[reporter_id])


class ReportImage(Base):
    __tablename__ = "report_images"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    storage_path = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(50), nullable=False, default="image/webp")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    report = relationship("Report", back_populates="images")

