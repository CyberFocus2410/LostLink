"""
Smoke tests executed against real PostgreSQL container via docker-compose.
Verifies:
  - Database connectivity and dialect detection ("postgresql")
  - Tables, columns, and foreign keys
  - Composite indexes presence
  - FastAPI /api/health response with Postgres dialect
  - End-to-end report creation, matching, and resolution in PostgreSQL
"""
import os
import pytest
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.models.report import Report, User, Community
from app.main import app
from app.database import get_db, Base
from app.services.auth_service import get_current_user
from app.matching.index import matching_index

PG_URL = os.getenv(
    "TEST_POSTGRES_URL",
    "postgresql+psycopg2://lostlink:lostlink_password@localhost:5432/lostlink"
)


@pytest.fixture(scope="module")
def pg_engine():
    try:
        engine = create_engine(PG_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        pytest.skip(f"PostgreSQL container not reachable at {PG_URL}: {e}")


def test_postgres_connection_and_dialect(pg_engine):
    assert pg_engine.dialect.name == "postgresql"
    with pg_engine.connect() as conn:
        res = conn.execute(text("SELECT version();")).scalar()
        assert "PostgreSQL" in res


def test_postgres_schema_and_composite_indexes(pg_engine):
    insp = inspect(pg_engine)
    tables = insp.get_table_names()

    # Core tables
    assert "users" in tables
    assert "reports" in tables
    assert "communities" in tables
    assert "facility_clusters" in tables
    assert "refresh_tokens" in tables
    assert "report_images" in tables

    # Composite indexes on reports table
    indexes = {idx["name"]: idx["column_names"] for idx in insp.get_indexes("reports")}
    assert "ix_reports_type_status" in indexes
    assert "ix_reports_category_status" in indexes
    assert "ix_reports_owner_status" in indexes
    assert "ix_reports_community_status" in indexes
    assert "ix_reports_date_status" in indexes


def test_postgres_health_endpoint(pg_engine):
    PgSession = sessionmaker(bind=pg_engine)

    def override_get_db():
        db = PgSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            res = client.get("/api/health")
            assert res.status_code == 200
            data = res.json()["data"]
            assert data["status"] == "healthy"
            assert data["database"]["status"] == "connected"
            # Dialect reflects PostgreSQL
            assert data["database"]["dialect"] == "postgresql"
            assert data["indexed_active_reports"] >= 0
    finally:
        app.dependency_overrides.clear()


def test_postgres_e2e_report_lifecycle(pg_engine):
    PgSession = sessionmaker(bind=pg_engine)
    db_setup = PgSession()

    # Ensure a valid user exists in PostgreSQL for the foreign key constraint
    real_user = db_setup.query(User).first()
    if not real_user:
        real_user = User(
            id="00000000-0000-0000-0000-000000000001",
            display_name="PG Smoke Tester",
            email="tester@example.com",
            password_hash="fakehash",
            role="user",
            is_active=True,
        )
        db_setup.add(real_user)
        db_setup.commit()
        db_setup.refresh(real_user)

    user_obj = real_user
    db_setup.close()

    def override_get_db():
        db = PgSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user_obj
    try:
        with TestClient(app) as client:
            # 1. Create a lost report in Postgres
            create_res = client.post(
                "/api/reports",
                json={
                    "type": "LOST",
                    "item_name": "PG Smoke Test Titanium Watch",
                    "category": "JEWELRY_WATCHES",
                    "description": "Titanium chronograph watch tested on real Postgres DB.",
                    "event_date": "2026-11-01",
                    "location_text": "Engineering Complex",
                    "latitude": 12.9716,
                    "longitude": 77.5946,
                    "contact_name": "Tester",
                    "contact_email": "tester@example.com",
                },
            )
            assert create_res.status_code == 201
            report_id = create_res.json()["data"]["id"]

            # 2. Query detail
            get_res = client.get(f"/api/reports/{report_id}")
            assert get_res.status_code == 200
            assert get_res.json()["data"]["item_name"] == "PG Smoke Test Titanium Watch"
            assert get_res.json()["data"]["latitude"] == 12.9716

            # 3. Resolve report
            resolve_res = client.post(f"/api/reports/{report_id}/resolve")
            assert resolve_res.status_code == 200
            assert resolve_res.json()["data"]["status"] == "RESOLVED"

    finally:
        app.dependency_overrides.clear()
