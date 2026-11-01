"""
Data migration script: SQLite -> PostgreSQL for LostLink.

Transfers all tables in dependency order:
  1. users
  2. refresh_tokens
  3. communities
  4. facility_clusters
  5. reports
  6. contact_requests
  7. report_flags

Usage:
  python scripts/migrate_sqlite_to_postgres.py \
    --sqlite-url sqlite:///lostlink.db \
    --postgres-url postgresql+psycopg2://lostlink:lostlink_password@localhost:5432/lostlink
"""
import sys
import argparse
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models.report import (
    Base,
    User,
    RefreshToken,
    Community,
    FacilityCluster,
    Report,
    ContactRequest,
    ReportFlag,
)
from app.database import normalize_database_url


def migrate(sqlite_url: str, postgres_url: str):
    print("=" * 70)
    print("LOSTLINK SQLITE -> POSTGRESQL DATA MIGRATION")
    print(f"Source SQLite:   {sqlite_url}")
    print(f"Target Postgres: {postgres_url}")
    print("=" * 70)

    # Source SQLite engine
    src_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    SrcSession = sessionmaker(bind=src_engine)
    src_db = SrcSession()

    # Target Postgres engine
    target_norm_url = normalize_database_url(postgres_url)
    tgt_engine = create_engine(target_norm_url, pool_pre_ping=True)
    TgtSession = sessionmaker(bind=tgt_engine)
    tgt_db = TgtSession()

    try:
        # Verify source connectivity
        src_db.execute(text("SELECT 1"))
        print("[OK] Source database connected.")

        # Verify target connectivity and ensure schema exists
        tgt_db.execute(text("SELECT 1"))
        print("[OK] Target database connected. Ensuring schema...")
        Base.metadata.create_all(bind=tgt_engine)
        print("[OK] Schema initialized on target.")

        # Table migration sequence in foreign-key dependency order
        models = [
            ("users", User),
            ("communities", Community),
            ("facility_clusters", FacilityCluster),
            ("reports", Report),
            ("refresh_tokens", RefreshToken),
            ("contact_requests", ContactRequest),
            ("report_flags", ReportFlag),
        ]

        total_migrated = 0

        for table_name, model in models:
            src_records = src_db.query(model).all()
            if not src_records:
                print(f"- {table_name:<20}: 0 records to migrate.")
                continue

            migrated_count = 0
            for record in src_records:
                # Check if already exists in target
                existing = tgt_db.query(model).filter(model.id == record.id).first()
                if not existing:
                    # Detach from source session and merge into target
                    record_dict = {c.name: getattr(record, c.name) for c in record.__table__.columns}
                    new_obj = model(**record_dict)
                    tgt_db.add(new_obj)
                    migrated_count += 1

            tgt_db.commit()
            print(f"[OK] {table_name:<20}: {migrated_count} of {len(src_records)} records transferred.")
            total_migrated += migrated_count

        print("=" * 70)
        print(f"MIGRATION COMPLETE: Successfully transferred {total_migrated} total records.")
        print("=" * 70)

    except Exception as e:
        tgt_db.rollback()
        print(f"\n[ERROR] Migration failed: {e}", file=sys.stderr)
        raise
    finally:
        src_db.close()
        tgt_db.close()


def main():
    parser = argparse.ArgumentParser(description="Migrate LostLink data from SQLite to PostgreSQL")
    parser.add_argument(
        "--sqlite-url",
        default=f"sqlite:///{backend_dir / 'lostlink.db'}",
        help="Source SQLite database URL",
    )
    parser.add_argument(
        "--postgres-url",
        default="postgresql+psycopg2://lostlink:lostlink_password@localhost:5432/lostlink",
        help="Target PostgreSQL database URL",
    )
    args = parser.parse_args()
    migrate(args.sqlite_url, args.postgres_url)


if __name__ == "__main__":
    main()

