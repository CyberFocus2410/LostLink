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
    def create_report(db: Session, data: ReportCreate) -> Report:
        """Validates, persists in SQLite, and updates in-memory DSA indexes."""
        report_dict = data.model_dump()
        report_dict["normalized_location"] = normalize_location(data.location_text)
        report_dict["type"] = data.type.value
        report_dict["category"] = data.category.value
        report_dict["status"] = "ACTIVE"

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

        # Run DSA matching engine
        ranked_matches, pool_size = MatchingEngine.match_report(
            source=source_record,
            limit=limit,
            min_score=min_score,
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
        """Rebuilds in-memory index from SQLite database."""
        reports = db.query(Report).all()
        matching_index.rebuild(reports)
        return len(reports)
