"""
Pydantic schemas for Community and FacilityCluster models.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class CommunityCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        s = v.strip().lower()
        import re
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", s):
            raise ValueError("Slug must be lowercase alphanumeric with hyphens (e.g. 'main-campus')")
        return s


class CommunityOut(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FacilityClusterCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    aliases: List[str] = Field(..., min_length=1)

    @field_validator("aliases")
    @classmethod
    def clean_aliases(cls, v: List[str]) -> List[str]:
        cleaned = [a.strip().lower() for a in v if a.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty alias is required")
        return cleaned


class FacilityClusterOut(BaseModel):
    id: str
    community_id: str
    name: str
    aliases: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

