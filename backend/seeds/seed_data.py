"""
Seed script for LostLink.
Populates realistic campus demo reports, matching pairs, and control cases.
"""
import sys
from pathlib import Path
from datetime import date, timedelta

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal, Base, engine
from app.models.report import Report, Community, FacilityCluster
from app.matching.heuristics import normalize_location, LOCATION_CLUSTERS
from app.matching.index import matching_index, ReportRecord
import json


SEED_REPORTS = [
    # Pair 1: MacBook Pro (Lost vs Found - strong match)
    {
        "type": "LOST",
        "item_name": "Space Gray MacBook Pro 14-inch",
        "category": "ELECTRONICS",
        "description": "Left my Apple MacBook Pro 14 M2 in a navy blue felt sleeve on a wooden desk. Has a small GitHub octocat sticker on bottom left corner.",
        "days_ago": 1,
        "location_text": "Main Library 2nd Floor Study Hall",
        "contact_name": "Aarav Sharma",
        "contact_email": "aarav.sharma@campus.edu",
        "contact_phone": "+1-555-0192",
        "status": "ACTIVE",
    },
    {
        "type": "FOUND",
        "item_name": "Apple MacBook Pro Laptop in Blue Sleeve",
        "category": "ELECTRONICS",
        "description": "Found a 14-inch space gray MacBook laptop left unattended on table 14. Stored inside a dark blue protective sleeve with sticker.",
        "days_ago": 1,
        "location_text": "Library 2nd Floor Quiet Study",
        "contact_name": "Campus Security Desk",
        "contact_email": "security@campus.edu",
        "contact_phone": "+1-555-0100",
        "status": "ACTIVE",
    },

    # Pair 2: Leather Wallet (Lost vs Found - exact location & terms)
    {
        "type": "LOST",
        "item_name": "Brown Leather Bi-fold Wallet",
        "category": "BAGS_WALLETS",
        "description": "Brown Bellroy leather wallet containing student campus ID card, MetroCard, and driver license. Very important.",
        "days_ago": 2,
        "location_text": "Student Center Food Court",
        "contact_name": "Elena Rostova",
        "contact_email": "elena.r@campus.edu",
        "contact_phone": "+1-555-0144",
        "status": "ACTIVE",
    },
    {
        "type": "FOUND",
        "item_name": "Brown Men's Leather Wallet with ID Cards",
        "category": "BAGS_WALLETS",
        "description": "Handed into cashier at dining hall. Dark brown bi-fold wallet with student ID cards and metro pass inside.",
        "days_ago": 2,
        "location_text": "Student Union Cafeteria",
        "contact_name": "Dining Staff Services",
        "contact_email": "dining@campus.edu",
        "contact_phone": "+1-555-0112",
        "status": "ACTIVE",
    },

    # Pair 3: Car Key fob (Lost vs Found - adjacent locations)
    {
        "type": "LOST",
        "item_name": "Honda Key Fob on Red Lanyard",
        "category": "KEYS_CARDS",
        "description": "Black Honda remote car key fob with physical metal key and a bright red University gym lanyard with carabiner.",
        "days_ago": 3,
        "location_text": "Recreation Center Locker Room",
        "contact_name": "Marcus Vance",
        "contact_email": "m.vance@campus.edu",
        "contact_phone": None,
        "status": "ACTIVE",
    },
    {
        "type": "FOUND",
        "item_name": "Automotive Car Key with Red University Lanyard",
        "category": "KEYS_CARDS",
        "description": "Found key ring with Honda remote clicker and red lanyard by the gym entrance bench.",
        "days_ago": 3,
        "location_text": "Sports Complex Fitness Center",
        "contact_name": "Rec Center Attendant",
        "contact_email": "recreation@campus.edu",
        "contact_phone": "+1-555-0188",
        "status": "ACTIVE",
    },

    # Pair 4: Hydro Flask Water Bottle (Partial / general match)
    {
        "type": "LOST",
        "item_name": "Olive Green Hydro Flask 32oz",
        "category": "OTHER",
        "description": "Olive green 32oz wide mouth insulated water bottle with black flex cap and yellow national parks sticker.",
        "days_ago": 4,
        "location_text": "Science Hall Room 204",
        "contact_name": "Priya Patel",
        "contact_email": "priya.p@campus.edu",
        "contact_phone": None,
        "status": "ACTIVE",
    },
    {
        "type": "FOUND",
        "item_name": "Green Metal Insulated Flask",
        "category": "OTHER",
        "description": "Found green metal drink bottle left on podium after lecture. Has sticker decals on side.",
        "days_ago": 4,
        "location_text": "Physics Lab Tech Wing",
        "contact_name": "Lab Tech Support",
        "contact_email": "physics.lab@campus.edu",
        "contact_phone": None,
        "status": "ACTIVE",
    },

    # Unrelated control case (different category, location, date)
    {
        "type": "FOUND",
        "item_name": "Gold Rimmed Reading Glasses in Black Case",
        "category": "JEWELRY_WATCHES",
        "description": "Found prescription reading glasses with thin metallic gold frames inside a hard clamshell case.",
        "days_ago": 7,
        "location_text": "Admin Building Bursar Office",
        "contact_name": "Reception Desk",
        "contact_email": "admin.desk@campus.edu",
        "contact_phone": "+1-555-0120",
        "status": "ACTIVE",
    },

    # Resolved report (demonstrating resolution lifecycle)
    {
        "type": "LOST",
        "item_name": "AirPods Pro 2nd Gen in White Case",
        "category": "ELECTRONICS",
        "description": "Lost AirPods Pro earbuds in charging case. Case has tiny engraving 'JD'.",
        "days_ago": 10,
        "location_text": "Campus Green Lawn",
        "contact_name": "Jack Davies",
        "contact_email": "jack.d@campus.edu",
        "contact_phone": "+1-555-0177",
        "status": "RESOLVED",
    },
]


def seed_database():
    """Seeds the SQLite database and refreshes matching index."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Ensure default community exists
        default_community = db.query(Community).filter(Community.slug == "main-campus").first()
        if not default_community:
            default_community = Community(
                name="Main Campus",
                slug="main-campus",
                description="Default university campus community",
                is_active=True,
            )
            db.add(default_community)
            db.commit()
            db.refresh(default_community)

            # Seed default facility clusters
            for cluster_name, aliases in LOCATION_CLUSTERS.items():
                fc = FacilityCluster(
                    community_id=default_community.id,
                    name=cluster_name.replace("_", " ").title(),
                    aliases=json.dumps(sorted(list(aliases))),
                )
                db.add(fc)
            db.commit()

        # Check if already seeded
        existing_count = db.query(Report).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} reports. Re-indexing...")
            reports = db.query(Report).all()
            matching_index.rebuild(reports)
            print(f"Successfully indexed {len(reports)} records.")
            return

        today = date.today()
        created_reports = []

        for item in SEED_REPORTS:
            days = item.pop("days_ago", 0)
            event_date = today - timedelta(days=days)
            loc_text = item["location_text"]
            norm_loc = normalize_location(loc_text)

            report = Report(
                type=item["type"],
                item_name=item["item_name"],
                category=item["category"],
                description=item["description"],
                event_date=event_date,
                location_text=loc_text,
                normalized_location=norm_loc,
                contact_name=item["contact_name"],
                contact_email=item["contact_email"],
                contact_phone=item.get("contact_phone"),
                status=item["status"],
                community_id=default_community.id,
            )
            db.add(report)
            created_reports.append(report)

        db.commit()
        for r in created_reports:
            db.refresh(r)

        matching_index.rebuild(created_reports)
        print(f"Successfully seeded {len(created_reports)} reports into SQLite and built DSA indexes.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
