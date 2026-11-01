"""
Community and Facility Cluster API endpoints for LostLink.
Supports multi-community tenancy and per-community facility cluster definitions.
"""
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import APIResponse
from app.schemas.community import (
    CommunityCreate,
    CommunityOut,
    FacilityClusterCreate,
    FacilityClusterOut,
)
from app.repositories.community_repo import CommunityRepository
from app.services.auth_service import get_current_user, require_admin

router = APIRouter(prefix="/communities", tags=["Communities"])


@router.get("", response_model=APIResponse[List[CommunityOut]])
def list_communities(db: Session = Depends(get_db)):
    """List all active communities."""
    communities = CommunityRepository.list_active(db)
    data = [CommunityOut.model_validate(c) for c in communities]
    return APIResponse.success(data=data)


@router.post("", response_model=APIResponse[CommunityOut], status_code=status.HTTP_201_CREATED)
def create_community(
    payload: CommunityCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Create a new community. Requires authentication."""
    existing = CommunityRepository.get_by_slug(db, payload.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Community with slug '{payload.slug}' already exists",
        )
    community = CommunityRepository.create(
        db,
        {
            "name": payload.name,
            "slug": payload.slug,
            "description": payload.description,
            "is_active": True,
        },
    )
    return APIResponse.success(data=CommunityOut.model_validate(community))


@router.get("/{identifier}/clusters", response_model=APIResponse[List[FacilityClusterOut]])
def list_community_clusters(
    identifier: str,
    db: Session = Depends(get_db),
):
    """List facility clusters for a community identified by UUID or slug."""
    community = CommunityRepository.get_by_id_or_slug(db, identifier)
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Community '{identifier}' not found",
        )
    clusters = CommunityRepository.list_clusters(db, community.id)
    out = []
    for c in clusters:
        aliases = json.loads(c.aliases) if isinstance(c.aliases, str) else c.aliases
        out.append(
            FacilityClusterOut(
                id=c.id,
                community_id=c.community_id,
                name=c.name,
                aliases=aliases,
                created_at=c.created_at,
            )
        )
    return APIResponse.success(data=out)


@router.post("/{identifier}/clusters", response_model=APIResponse[FacilityClusterOut], status_code=status.HTTP_201_CREATED)
def create_community_cluster(
    identifier: str,
    payload: FacilityClusterCreate,
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin),
):
    """Define a new facility cluster for a community. Admin/moderator only."""
    community = CommunityRepository.get_by_id_or_slug(db, identifier)
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Community '{identifier}' not found",
        )
    cluster = CommunityRepository.create_cluster(
        db,
        community_id=community.id,
        name=payload.name,
        aliases=payload.aliases,
    )
    aliases = json.loads(cluster.aliases) if isinstance(cluster.aliases, str) else cluster.aliases
    return APIResponse.success(
        data=FacilityClusterOut(
            id=cluster.id,
            community_id=cluster.community_id,
            name=cluster.name,
            aliases=aliases,
            created_at=cluster.created_at,
        )
    )

