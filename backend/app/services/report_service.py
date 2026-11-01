"""
Service layer coordinating report lifecycle, database transactions, and DSA matching indexes.
"""
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.repositories.report_repo import ReportRepository
from app.models.report import Report, ContactRequest, ReportFlag
from app.schemas.report import ReportCreate, ReportUpdate, ReportOut
from app.schemas.match import MatchListOut, MatchResultItem, MatchComponentScores
from app.schemas.contact import ContactRequestCreate, ReportFlagCreate
from app.matching.heuristics import normalize_location
from app.matching.index import ReportRecord, matching_index
from app.matching.engine import MatchingEngine


class ReportService:
    @staticmethod
    def create_report(db: Session, data: ReportCreate, owner_id: str | None = None) -> Report:
        """Validates, persists, and updates in-memory DSA indexes.
        owner_id is optional for backward compat with seed data and tests."""
        report_dict = data.model_dump()
        report_dict["normalized_location"] = normalize_location(data.location_text)
        report_dict["type"] = data.type.value
        report_dict["category"] = data.category.value
        report_dict["status"] = "ACTIVE"
        if owner_id:
            report_dict["owner_id"] = owner_id

        report = ReportRepository.create(db, report_dict)

        # Index new active report
        record = ReportRecord.from_model(report)
        matching_index.add(record)

        return report

    @staticmethod
    def get_report(db: Session, report_id: str) -> Optional[Report]:
        return ReportRepository.get_by_id(db, report_id)

    @staticmethod
    def list_reports(
        db: Session,
        *,
        q: Optional[str] = None,
        report_type: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        date_from=None,
        date_to=None,
        location: Optional[str] = None,
        owner_id: Optional[str] = None,
        community_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        sort: str = "date_desc",
    ) -> Tuple[List[Report], int]:
        return ReportRepository.list_reports(
            db,
            q=q,
            report_type=report_type,
            category=category,
            status=status,
            date_from=date_from,
            date_to=date_to,
            location=location,
            owner_id=owner_id,
            community_id=community_id,
            page=page,
            limit=limit,
            sort=sort,
        )

    @staticmethod
    def update_report(db: Session, report_id: str, data: ReportUpdate) -> Optional[Report]:
        report = ReportRepository.get_by_id(db, report_id)
        if not report:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        if "location_text" in update_dict and update_dict["location_text"]:
            update_dict["normalized_location"] = normalize_location(update_dict["location_text"])
        if "category" in update_dict and update_dict["category"]:
            update_dict["category"] = update_dict["category"].value
        if "status" in update_dict and update_dict["status"]:
            update_dict["status"] = update_dict["status"].value

        updated = ReportRepository.update(db, report, update_dict)

        # Refresh index
        record = ReportRecord.from_model(updated)
        matching_index.update(record)

        return updated

    @staticmethod
    def resolve_report(db: Session, report_id: str) -> Optional[Report]:
        report = ReportRepository.get_by_id(db, report_id)
        if not report:
            return None

        resolved = ReportRepository.resolve(db, report)

        # Remove from active matching index
        record = ReportRecord.from_model(resolved)
        matching_index.update(record)

        return resolved

    @classmethod
    def get_matches(
        cls,
        db: Session,
        report_id: str,
        limit: int = 5,
        min_score: float = 0.0,
    ) -> Optional[MatchListOut]:
        report = ReportRepository.get_by_id(db, report_id)
        if not report:
            return None

        # Ensure in-memory record is current
        source_record = matching_index.get(report_id)
        if not source_record:
            source_record = ReportRecord.from_model(report)
            matching_index.add(source_record)

        # Check for community-specific facility clusters in database
        custom_clusters = None
        if getattr(report, "community_id", None):
            from app.models.report import FacilityCluster
            import json
            db_clusters = db.query(FacilityCluster).filter(FacilityCluster.community_id == report.community_id).all()
            if db_clusters:
                custom_clusters = {}
                for c in db_clusters:
                    try:
                        aliases_list = json.loads(c.aliases)
                    except Exception:
                        aliases_list = [a.strip().lower() for a in c.aliases.split(",") if a.strip()]
                    custom_clusters[c.name.lower()] = set(aliases_list)

        # Run DSA matching engine
        ranked_matches, pool_size = MatchingEngine.match_report(
            source=source_record,
            limit=limit,
            min_score=min_score,
            custom_clusters=custom_clusters,
        )

        match_items: List[MatchResultItem] = []
        for match in ranked_matches:
            cand_model = ReportRepository.get_by_id(db, match.candidate_id)
            if not cand_model:
                continue

            match_items.append(
                MatchResultItem(
                    candidate=ReportOut.model_validate(cand_model),
                    total_score=match.total_score,
                    components=MatchComponentScores(
                        category_score=match.category_score,
                        location_score=match.location_score,
                        date_score=match.date_score,
                        keyword_score=match.keyword_score,
                    ),
                    shared_keywords=match.shared_keywords,
                    reasons=match.reasons,
                    disclaimer=match.disclaimer,
                )
            )

        return MatchListOut(
            source_report=ReportOut.model_validate(report),
            matches=match_items,
            candidate_count=pool_size,
        )

    @staticmethod
    def create_contact_request(db: Session, data: ContactRequestCreate) -> ContactRequest:
        req_dict = data.model_dump()
        return ReportRepository.create_contact_request(db, req_dict)

    @staticmethod
    def flag_report(db: Session, report_id: str, data: ReportFlagCreate) -> ReportFlag:
        flag_dict = {"report_id": report_id, "reason": data.reason}
        return ReportRepository.create_flag(db, flag_dict)

    @staticmethod
    def rebuild_all_indexes(db: Session) -> int:
        """Rebuilds in-memory index from database ACTIVE reports only."""
        reports = db.query(Report).filter(Report.status == "ACTIVE").all()
        matching_index.rebuild(reports)
        return len(reports)

    @staticmethod
    def add_report_image(
        db: Session,
        report_id: str,
        file_bytes: bytes,
        original_filename: str,
        content_type: str,
    ):
        report = ReportRepository.get_by_id(db, report_id)
        if not report:
            raise ValueError(f"Report '{report_id}' not found.")
        if len(report.images) >= 3:
            raise ValueError("Maximum 3 images allowed per report.")

        from app.services.image_service import ImageService
        from app.services.storage import get_storage_provider
        from app.models.report import ReportImage

        main_bytes, thumb_bytes, path_main, path_thumb, out_mime = ImageService.validate_and_process_image(
            file_bytes, original_filename, content_type
        )

        storage = get_storage_provider()
        image_url = storage.upload_file(main_bytes, path_main, out_mime)
        thumb_url = storage.upload_file(thumb_bytes, path_thumb, out_mime)

        image_record = ReportImage(
            report_id=report_id,
            image_url=image_url,
            thumbnail_url=thumb_url,
            storage_path=path_main,
            file_size=len(main_bytes),
            content_type=out_mime,
        )
        db.add(image_record)
        db.commit()
        db.refresh(image_record)
        return image_record

    @staticmethod
    def delete_report_image(db: Session, report_id: str, image_id: str) -> bool:
        from app.models.report import ReportImage
        from app.services.storage import get_storage_provider

        image = db.query(ReportImage).filter(
            ReportImage.id == image_id,
            ReportImage.report_id == report_id
        ).first()
        if not image:
            return False

        storage = get_storage_provider()
        try:
            storage.delete_file(image.storage_path)
            thumb_path = image.storage_path.replace(".webp", "_thumb.webp")
            storage.delete_file(thumb_path)
        except Exception:
            pass

        db.delete(image)
        db.commit()
        return True
