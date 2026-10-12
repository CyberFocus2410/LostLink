"""
Tests verifying SQLite persistence and index rebuild across server restarts.
"""
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.report import Report
from app.matching.heuristics import normalize_location
from app.matching.index import MatchingIndex, ReportRecord
from app.services.report_service import ReportService


def test_sqlite_persistence_and_index_rebuild(tmp_path):
    # Setup temporary SQLite file database
    db_file = tmp_path / "test_lostlink.db"
    db_url = f"sqlite:///{db_file}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    Session = sessionmaker(bind=test_engine)

    # 1. First session: Create records
    db1 = Session()
    report1 = Report(
        type="LOST",
        item_name="Sony WH-1000XM5 Headphones",
        category="ELECTRONICS",
        description="Black noise cancelling wireless headphones in zipper travel case.",
        event_date=date.today(),
        location_text="Library 3rd Floor",
        normalized_location=normalize_location("Library 3rd Floor"),
        contact_name="Frank",
        contact_email="frank@campus.edu",
        status="ACTIVE",
    )
    db1.add(report1)
    db1.commit()
    report1_id = report1.id
    db1.close()

    # Dispose engine to simulate complete backend shutdown
    test_engine.dispose()

    # 2. Second session (simulating restart): New engine & session
    restarted_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    RestartedSession = sessionmaker(bind=restarted_engine)
    db2 = RestartedSession()

    # Verify report is still in SQLite
    persisted = db2.query(Report).filter(Report.id == report1_id).first()
    assert persisted is not None
    assert persisted.item_name == "Sony WH-1000XM5 Headphones"
    assert persisted.category == "ELECTRONICS"

    # Rebuild a fresh index from restarted database
    fresh_index = MatchingIndex()
    reports = db2.query(Report).all()
    fresh_index.rebuild(reports)

    # Check indexed status
    assert len(fresh_index.records) == 1
    assert "ELECTRONICS" in fresh_index.category_index
    assert report1_id in fresh_index.category_index["ELECTRONICS"]
    assert "sony" in fresh_index.keyword_index

    db2.close()
    restarted_engine.dispose()
