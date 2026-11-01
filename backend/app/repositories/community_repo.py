"""
Repository layer for Communities and Facility Clusters.
"""
import json
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.report import Community, FacilityCluster


class CommunityRepository:
    @staticmethod
    def list_active(db: Session) -> List[Community]:
        return db.query(Community).filter(Community.is_active == True).order_by(Community.name).all()

    @staticmethod
    def get_by_id(db: Session, community_id: str) -> Optional[Community]:
        return db.query(Community).filter(Community.id == community_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Community]:
        return db.query(Community).filter(Community.slug == slug.lower()).first()

    @staticmethod
    def get_by_id_or_slug(db: Session, identifier: str) -> Optional[Community]:
        return (
            db.query(Community)
            .filter((Community.id == identifier) | (Community.slug == identifier.lower()))
            .first()
        )

    @staticmethod
    def create(db: Session, data: dict) -> Community:
        community = Community(**data)
        db.add(community)
        db.commit()
        db.refresh(community)
        return community

    @staticmethod
    def list_clusters(db: Session, community_id: str) -> List[FacilityCluster]:
        return (
            db.query(FacilityCluster)
            .filter(FacilityCluster.community_id == community_id)
            .order_by(FacilityCluster.name)
            .all()
        )

    @staticmethod
    def create_cluster(db: Session, community_id: str, name: str, aliases: List[str]) -> FacilityCluster:
        cluster = FacilityCluster(
            community_id=community_id,
            name=name,
            aliases=json.dumps(aliases),
        )
        db.add(cluster)
        db.commit()
        db.refresh(cluster)
        return cluster

