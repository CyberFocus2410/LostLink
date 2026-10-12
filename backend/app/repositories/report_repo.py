"""
Repository layer for reports, handling database transactions and queries.
"""
from datetime import date
from typing import Optional, Tuple
from sqlalchemy import or_, desc, asc, func
from sqlalchemy.orm import Session
from app.models.report import Report, ContactRequest, ReportFlag


class ReportRepository:
    @staticmethod
    def create(db: Session, report_data: dict) -> Report:
        report = Report(**report_data)
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_by_id(db: Session, report_id: str) -> Optional[Report]:
        return db.query(Report).filter(Report.id == report_id).first()

    @staticmethod
    def list_reports(
        db: Session,
        *,
        q: Optional[str] = None,
        report_type: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        sort: str = "date_desc",
    ) -> Tuple[list[Report], int]:
        query = db.query(Report)

        # Filters
        if report_type:
            query = query.filter(Report.type == report_type)
        if category:
            query = query.filter(Report.category == category)
        if status:
            query = query.filter(Report.status == status)
        if date_from:
            query = query.filter(Report.event_date >= date_from)
        if date_to:
            query = query.filter(Report.event_date <= date_to)
        if location:
            query = query.filter(Report.location_text.ilike(f"%{location}%"))

        if q:
            term = f"%{q.strip()}%"
            query = query.filter(
                or_(
                    Report.item_name.ilike(term),
                    Report.description.ilike(term),
                    Report.location_text.ilike(term),
                )
            )

        total = query.count()

        # Sorting
        if sort == "date_desc":
            query = query.order_by(desc(Report.event_date), desc(Report.created_at))
        elif sort == "date_asc":
            query = query.order_by(asc(Report.event_date), asc(Report.created_at))
        elif sort == "created_asc":
            query = query.order_by(asc(Report.created_at))
        else:  # default created_desc
            query = query.order_by(desc(Report.created_at))

        # Pagination
        offset = max(0, (page - 1) * limit)
        items = query.offset(offset).limit(limit).all()

        return items, total

    @staticmethod
    def update(db: Session, report: Report, update_data: dict) -> Report:
        for key, value in update_data.items():
            if hasattr(report, key) and value is not None:
                setattr(report, key, value)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def resolve(db: Session, report: Report) -> Report:
        report.status = "RESOLVED"
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_all_active_reports(db: Session) -> list[Report]:
        return db.query(Report).filter(Report.status == "ACTIVE").all()

    @staticmethod
    def get_all_active_opposite_reports(db: Session, opposite_type: str) -> list[Report]:
        return (
            db.query(Report)
            .filter(Report.status == "ACTIVE", Report.type == opposite_type)
            .all()
        )

    @staticmethod
    def create_contact_request(db: Session, data: dict) -> ContactRequest:
        req = ContactRequest(**data)
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def create_flag(db: Session, data: dict) -> ReportFlag:
        flag = ReportFlag(**data)
        db.add(flag)
        db.commit()
        db.refresh(flag)
        return flag
