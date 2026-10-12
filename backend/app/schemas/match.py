"""
Pydantic schemas for Match results and score breakdowns.
"""
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.report import ReportOut


class MatchComponentScores(BaseModel):
    category_score: float = Field(..., ge=0, le=100)
    location_score: float = Field(..., ge=0, le=100)
    date_score: float = Field(..., ge=0, le=100)
    keyword_score: float = Field(..., ge=0, le=100)


class MatchResultItem(BaseModel):
    candidate: ReportOut
    total_score: float = Field(..., ge=0, le=100)
    components: MatchComponentScores
    shared_keywords: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    disclaimer: str = "Potential match—not verified ownership"


class MatchListOut(BaseModel):
    source_report: ReportOut
    matches: list[MatchResultItem] = Field(default_factory=list)
    candidate_count: int
