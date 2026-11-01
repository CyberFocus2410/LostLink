"""
Privacy-Preserving Product Analytics for LostLink.
Strictly aggregates system metrics and records anonymous events
without collecting IP addresses, cookies, user identifiers, or PII.
"""
import logging
from collections import Counter
from typing import Dict
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.report import Report, Community
from app.schemas.common import APIResponse

logger = logging.getLogger("LostLink.Analytics")
router = APIRouter(prefix="/analytics", tags=["Analytics"])

# In-memory aggregate event counter for lightweight anonymous metrics
_event_counters: Counter = Counter()


class AnonymousEventPayload(BaseModel):
    event_name: str = Field(..., max_length=64, pattern=r"^[a-z0-9_\-]+$")


@router.post("/event", response_model=APIResponse[dict])
def record_anonymous_event(payload: AnonymousEventPayload):
    """
    Records an anonymous telemetry event (e.g. 'match_clicked', 'pwa_installed').
    Zero PII or user tracking.
    """
    _event_counters[payload.event_name] += 1
    logger.info(f"[Anonymous Analytics] Event: {payload.event_name}")
    return APIResponse.success(data={"recorded": True, "event": payload.event_name})


@router.get("/summary", response_model=APIResponse[dict])
def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Returns high-level aggregate product metrics without personal data.
    """
    active_count = db.query(Report).filter(Report.status == "ACTIVE").count()
    resolved_count = db.query(Report).filter(Report.status == "RESOLVED").count()
    lost_count = db.query(Report).filter(Report.status == "ACTIVE", Report.type == "LOST").count()
    found_count = db.query(Report).filter(Report.status == "ACTIVE", Report.type == "FOUND").count()
    communities_count = db.query(Community).filter(Community.is_active == True).count()

    return APIResponse.success(data={
        "active_reports": active_count,
        "resolved_reports": resolved_count,
        "active_lost": lost_count,
        "active_found": found_count,
        "active_communities": communities_count,
        "anonymous_events": dict(_event_counters.most_common(20)),
    })

