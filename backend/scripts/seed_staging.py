"""
Staging Seed Script for LostLink.
Populates realistic campus communities, facility clusters, users, reports,
abuse flags, and contact requests for staging QA and demo verification.
"""
import sys
import json
from pathlib import Path
from datetime import date, datetime, timedelta, timezone

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal, Base, engine
from app.models.report import Report, Community, FacilityCluster, User, ContactRequest, ReportFlag
from app.services.auth_service import hash_password
from app.services.report_service import ReportService
from app.matching.heuristics import normalize_location
from app.matching.index import matching_index, ReportRecord


def seed_staging():
    print("[LostLink Staging Seed] Starting staging database seed...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Communities
        communities_data = [
            {
                "id": "comm-central-campus",
                "name": "Central University Campus",
                "slug": "central-campus",
                "description": "Main collegiate campus including central library, student union, and science quad.",
            },
            {
                "id": "comm-tech-park",
                "name": "Innovation Tech Park",
                "slug": "tech-park",
                "description": "Research and engineering innovation park adjacent to campus.",
            },
        ]

        communities = {}
        for c in communities_data:
            existing = db.query(Community).filter(Community.id == c["id"]).first()
            if not existing:
                comm = Community(
                    id=c["id"],
                    name=c["name"],
                    slug=c["slug"],
                    description=c["description"],
                    is_active=True,
                )
                db.add(comm)
                db.flush()
                communities[c["slug"]] = comm
            else:
                communities[c["slug"]] = existing

        # 2. Seed Facility Clusters
        clusters_data = [
            ("comm-central-campus", "Main Library", ["library", "2nd floor quiet study", "study carrels", "stacks"]),
            ("comm-central-campus", "Student Union", ["cafeteria", "food court", "student center", "dining"]),
            ("comm-central-campus", "Science & Engineering Complex", ["science hall", "engineering lab", "lab 101"]),
            ("comm-central-campus", "Athletic Pavilion", ["gym", "rec center", "bleachers", "fitness center"]),
            ("comm-tech-park", "Building Alpha", ["alpha lobby", "tower a", "atrium"]),
            ("comm-tech-park", "Research Labs", ["clean room", "hardware lab", "maker space"]),
        ]

        for comm_id, name, aliases in clusters_data:
            exists = db.query(FacilityCluster).filter(
                FacilityCluster.community_id == comm_id,
                FacilityCluster.name == name,
            ).first()
            if not exists:
                fc = FacilityCluster(
                    community_id=comm_id,
                    name=name,
                    aliases=json.dumps(aliases),
                )
                db.add(fc)

        db.commit()

        # 3. Seed Users
        users_data = [
            {
                "id": "user-admin-01",
                "email": "admin@lostlink.org",
                "display_name": "Admin Moderator",
                "password": "Admin123!",
                "role": "admin",
            },
            {
                "id": "user-alex-02",
                "email": "alex.chen@university.edu",
                "display_name": "Alex Chen",
                "password": "Student123!",
                "role": "user",
            },
            {
                "id": "user-maya-03",
                "email": "maya.patel@university.edu",
                "display_name": "Maya Patel",
                "password": "Student123!",
                "role": "user",
            },
            {
                "id": "user-jordan-04",
                "email": "jordan.lee@university.edu",
                "display_name": "Jordan Lee",
                "password": "Student123!",
                "role": "user",
            },
            {
                "id": "user-spammer-05",
                "email": "spammer@sketchy.io",
                "display_name": "Suspicious Bot",
                "password": "Spam123!",
                "role": "user",
            },
        ]

        users = {}
        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                new_user = User(
                    id=u["id"],
                    email=u["email"],
                    display_name=u["display_name"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                    is_active=True,
                )
                db.add(new_user)
                db.flush()
                users[u["email"]] = new_user
            else:
                users[u["email"]] = existing

        db.commit()

        # 4. Seed Reports
        today = date.today()
        reports_data = [
            # Pair 1: MacBook Pro (Lost vs Found - strong match ~95)
            {
                "id": "rep-staging-mbp-lost",
                "owner_id": users["alex.chen@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "Space Gray MacBook Pro 14-inch",
                "category": "ELECTRONICS",
                "description": "Left my 14-inch M3 MacBook Pro in dark gray felt sleeve with GitHub octocat sticker on desk.",
                "event_date": today - timedelta(days=1),
                "location_text": "Main Library 2nd Floor Study Carrel",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "contact_name": "Alex Chen",
                "contact_email": "alex.chen@university.edu",
                "contact_phone": "+1-555-0101",
                "status": "ACTIVE",
            },
            {
                "id": "rep-staging-mbp-found",
                "owner_id": users["maya.patel@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "FOUND",
                "item_name": "Apple MacBook Pro Laptop in Felt Sleeve",
                "category": "ELECTRONICS",
                "description": "Found a 14-inch Apple MacBook Pro laptop inside dark gray sleeve on library desk, handed into circulation desk.",
                "event_date": today - timedelta(days=1),
                "location_text": "Library 2nd Floor Quiet Study Area",
                "latitude": 37.7750,
                "longitude": -122.4193,
                "contact_name": "Maya Patel",
                "contact_email": "maya.patel@university.edu",
                "contact_phone": "+1-555-0102",
                "status": "ACTIVE",
            },

            # Pair 2: Leather Wallet
            {
                "id": "rep-staging-wallet-lost",
                "owner_id": users["jordan.lee@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "Tan Leather Bellroy Bifold Wallet",
                "category": "BAGS_WALLETS",
                "description": "Tan leather wallet with student campus ID, driver license, and blue transit pass.",
                "event_date": today - timedelta(days=2),
                "location_text": "Student Union Cafeteria Food Court",
                "latitude": 37.7760,
                "longitude": -122.4180,
                "contact_name": "Jordan Lee",
                "contact_email": "jordan.lee@university.edu",
                "contact_phone": "+1-555-0103",
                "status": "ACTIVE",
            },
            {
                "id": "rep-staging-wallet-found",
                "owner_id": users["admin@lostlink.org"].id,
                "community_id": "comm-central-campus",
                "type": "FOUND",
                "item_name": "Brown Men's Leather Wallet with Campus ID",
                "category": "BAGS_WALLETS",
                "description": "Brown bifold wallet containing student cards and cards found near dining tables.",
                "event_date": today - timedelta(days=2),
                "location_text": "Student Union Food Court",
                "latitude": 37.7761,
                "longitude": -122.4179,
                "contact_name": "Admin Moderator",
                "contact_email": "admin@lostlink.org",
                "contact_phone": "+1-555-0100",
                "status": "ACTIVE",
            },

            # Pair 3: Brass Keys
            {
                "id": "rep-staging-keys-lost",
                "owner_id": users["alex.chen@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "Set of 3 Brass House Keys on Blue Carabiner",
                "category": "KEYS_CARDS",
                "description": "Three brass keys with a blue anodized carabiner clip and a white AirTag attached.",
                "event_date": today - timedelta(days=3),
                "location_text": "Athletic Pavilion Bleachers",
                "latitude": 37.7730,
                "longitude": -122.4200,
                "contact_name": "Alex Chen",
                "contact_email": "alex.chen@university.edu",
                "contact_phone": "+1-555-0101",
                "status": "ACTIVE",
            },
            {
                "id": "rep-staging-keys-found",
                "owner_id": users["jordan.lee@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "FOUND",
                "item_name": "Keys with Blue Clip and Tag",
                "category": "KEYS_CARDS",
                "description": "Found a ring of keys with a blue carabiner on the gym bleachers after basketball practice.",
                "event_date": today - timedelta(days=3),
                "location_text": "Athletic Pavilion Rec Center",
                "latitude": 37.7731,
                "longitude": -122.4202,
                "contact_name": "Jordan Lee",
                "contact_email": "jordan.lee@university.edu",
                "contact_phone": "+1-555-0103",
                "status": "ACTIVE",
            },

            # Pair 4: Hydro Flask Water Bottle
            {
                "id": "rep-staging-flask-lost",
                "owner_id": users["maya.patel@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "Lilac Purple Hydro Flask 32oz",
                "category": "OTHER",
                "description": "Lilac purple insulated water bottle with Yosemite and Joshua Tree national park stickers.",
                "event_date": today - timedelta(days=2),
                "location_text": "Science Complex Lab 101",
                "latitude": 37.7770,
                "longitude": -122.4160,
                "contact_name": "Maya Patel",
                "contact_email": "maya.patel@university.edu",
                "contact_phone": "+1-555-0102",
                "status": "ACTIVE",
            },
            {
                "id": "rep-staging-flask-found",
                "owner_id": users["alex.chen@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "FOUND",
                "item_name": "Purple Insulated Metal Water Bottle",
                "category": "OTHER",
                "description": "Found a 32oz purple vacuum flask with nature stickers left on lab counter.",
                "event_date": today - timedelta(days=2),
                "location_text": "Science Hall 1st Floor Hallway",
                "latitude": 37.7771,
                "longitude": -122.4159,
                "contact_name": "Alex Chen",
                "contact_email": "alex.chen@university.edu",
                "contact_phone": "+1-555-0101",
                "status": "ACTIVE",
            },

            # Pair 5: Sony Noise-Cancelling Headphones
            {
                "id": "rep-staging-sony-lost",
                "owner_id": users["jordan.lee@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "Sony WH-1000XM5 Wireless Headphones in Silver",
                "category": "ELECTRONICS",
                "description": "Silver over-ear noise-cancelling headphones inside gray zipper storage case.",
                "event_date": today - timedelta(days=1),
                "location_text": "Main Library 2nd Floor Study Carrel",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "contact_name": "Jordan Lee",
                "contact_email": "jordan.lee@university.edu",
                "contact_phone": "+1-555-0103",
                "status": "ACTIVE",
            },
            {
                "id": "rep-staging-sony-found",
                "owner_id": users["admin@lostlink.org"].id,
                "community_id": "comm-central-campus",
                "type": "FOUND",
                "item_name": "Silver Sony Over-Ear Bluetooth Headphones with Case",
                "category": "ELECTRONICS",
                "description": "Found premium silver Sony over-ear headphones in hard case left at study desk.",
                "event_date": today - timedelta(days=1),
                "location_text": "Library 2nd Floor Quiet Study Area",
                "latitude": 37.7750,
                "longitude": -122.4193,
                "contact_name": "Admin Moderator",
                "contact_email": "admin@lostlink.org",
                "contact_phone": "+1-555-0100",
                "status": "ACTIVE",
            },

            # Pair 6: Rain Jacket
            {
                "id": "rep-staging-jacket-blue-lost",
                "owner_id": users["alex.chen@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "Navy Blue Patagonia Torrentshell Rain Jacket",
                "category": "CLOTHING",
                "description": "Men's size M navy blue waterproof hooded shell jacket with gray zipper.",
                "event_date": today - timedelta(days=3),
                "location_text": "Student Union Cafeteria Food Court",
                "latitude": 37.7760,
                "longitude": -122.4180,
                "contact_name": "Alex Chen",
                "contact_email": "alex.chen@university.edu",
                "contact_phone": "+1-555-0101",
                "status": "ACTIVE",
            },
            {
                "id": "rep-staging-jacket-blue-found",
                "owner_id": users["maya.patel@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "FOUND",
                "item_name": "Dark Blue Hooded Rain Jacket found in Dining Hall",
                "category": "CLOTHING",
                "description": "Found a blue outdoor rain jacket draped over chair in the student center food court.",
                "event_date": today - timedelta(days=3),
                "location_text": "Student Union Food Court",
                "latitude": 37.7761,
                "longitude": -122.4179,
                "contact_name": "Maya Patel",
                "contact_email": "maya.patel@university.edu",
                "contact_phone": "+1-555-0102",
                "status": "ACTIVE",
            },

            # Pair 7: Graphing Calculator
            {
                "id": "rep-staging-calc-lost",
                "owner_id": users["maya.patel@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "Rose Gold TI-84 Plus CE Graphing Calculator",
                "category": "DOCUMENTS_BOOKS",
                "description": "Texas Instruments TI-84 color edition calculator in metallic rose gold with charging cord.",
                "event_date": today - timedelta(days=2),
                "location_text": "Science Complex Lab 101",
                "latitude": 37.7770,
                "longitude": -122.4160,
                "contact_name": "Maya Patel",
                "contact_email": "maya.patel@university.edu",
                "contact_phone": "+1-555-0102",
                "status": "ACTIVE",
            },
            {
                "id": "rep-staging-calc-found",
                "owner_id": users["jordan.lee@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "FOUND",
                "item_name": "Texas Instruments Color Graphing Calculator with Pink Cover",
                "category": "DOCUMENTS_BOOKS",
                "description": "TI-84 graphing calculator left under a lecture chair in the engineering wing.",
                "event_date": today - timedelta(days=2),
                "location_text": "Science Hall Classroom 102",
                "latitude": 37.7772,
                "longitude": -122.4162,
                "contact_name": "Jordan Lee",
                "contact_email": "jordan.lee@university.edu",
                "contact_phone": "+1-555-0103",
                "status": "ACTIVE",
            },

            # Pair 8: RFID Staff ID Badge
            {
                "id": "rep-staging-badge-lost",
                "owner_id": users["jordan.lee@university.edu"].id,
                "community_id": "comm-tech-park",
                "type": "LOST",
                "item_name": "Faculty Access RFID Keycard on Blue Campus Lanyard",
                "category": "KEYS_CARDS",
                "description": "White RFID proximity badge with university logo on a blue fabric breakaway lanyard.",
                "event_date": today - timedelta(days=1),
                "location_text": "Building Alpha Lobby",
                "latitude": 37.7800,
                "longitude": -122.4100,
                "contact_name": "Jordan Lee",
                "contact_email": "jordan.lee@university.edu",
                "contact_phone": "+1-555-0103",
                "status": "ACTIVE",
            },
            {
                "id": "rep-staging-badge-found",
                "owner_id": users["admin@lostlink.org"].id,
                "community_id": "comm-tech-park",
                "type": "FOUND",
                "item_name": "Blue University Lanyard with White Smart Access Badge",
                "category": "KEYS_CARDS",
                "description": "Found security badge with blue lanyard turned into building alpha front security.",
                "event_date": today - timedelta(days=1),
                "location_text": "Building Alpha Tower Atrium",
                "latitude": 37.7801,
                "longitude": -122.4101,
                "contact_name": "Admin Moderator",
                "contact_email": "admin@lostlink.org",
                "contact_phone": "+1-555-0100",
                "status": "ACTIVE",
            },

            # Pair 9: Prescription Eyeglasses
            {
                "id": "rep-staging-glasses-lost",
                "owner_id": users["alex.chen@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "Ray-Ban Clubmaster Eyeglasses in Tortoiseshell",
                "category": "JEWELRY_WATCHES",
                "description": "Brown tortoiseshell frame prescription glasses with gold bridge and black nose pads.",
                "event_date": today - timedelta(days=4),
                "location_text": "Athletic Pavilion Bleachers",
                "latitude": 37.7730,
                "longitude": -122.4200,
                "contact_name": "Alex Chen",
                "contact_email": "alex.chen@university.edu",
                "contact_phone": "+1-555-0101",
                "status": "ACTIVE",
            },
            {
                "id": "rep-staging-glasses-found",
                "owner_id": users["jordan.lee@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "FOUND",
                "item_name": "Brown Rimmed Prescription Glasses in Leather Case",
                "category": "JEWELRY_WATCHES",
                "description": "Found prescription reading glasses inside a black case near gymnasium courts.",
                "event_date": today - timedelta(days=4),
                "location_text": "Athletic Pavilion Rec Center",
                "latitude": 37.7731,
                "longitude": -122.4202,
                "contact_name": "Jordan Lee",
                "contact_email": "jordan.lee@university.edu",
                "contact_phone": "+1-555-0103",
                "status": "ACTIVE",
            },

            # Pair 10: Calculus Textbook
            {
                "id": "rep-staging-textbook-lost",
                "owner_id": users["maya.patel@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "Stewart Calculus Early Transcendentals 9th Edition Hardcover",
                "category": "DOCUMENTS_BOOKS",
                "description": "Heavy blue hardcover calculus textbook with handwritten study notes in margins.",
                "event_date": today - timedelta(days=5),
                "location_text": "Main Library 2nd Floor Study Carrel",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "contact_name": "Maya Patel",
                "contact_email": "maya.patel@university.edu",
                "contact_phone": "+1-555-0102",
                "status": "ACTIVE",
            },
            {
                "id": "rep-staging-textbook-found",
                "owner_id": users["admin@lostlink.org"].id,
                "community_id": "comm-central-campus",
                "type": "FOUND",
                "item_name": "Heavy Math Calculus Textbook Left on Desk",
                "category": "DOCUMENTS_BOOKS",
                "description": "Stewart Calculus hardcover book left overnight in the library study carrels.",
                "event_date": today - timedelta(days=5),
                "location_text": "Library 2nd Floor Quiet Study Area",
                "latitude": 37.7750,
                "longitude": -122.4193,
                "contact_name": "Admin Moderator",
                "contact_email": "admin@lostlink.org",
                "contact_phone": "+1-555-0100",
                "status": "ACTIVE",
            },

            # Pair 11: Apple Watch
            {
                "id": "rep-staging-watch-lost",
                "owner_id": users["jordan.lee@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "Apple Watch Series 8 Midnight 45mm with Sport Band",
                "category": "JEWELRY_WATCHES",
                "description": "Dark midnight aluminum smartwatch with black silicone sport band and small scratch on bottom right bezel.",
                "event_date": today - timedelta(days=3),
                "location_text": "Athletic Pavilion Bleachers",
                "latitude": 37.7730,
                "longitude": -122.4200,
                "contact_name": "Jordan Lee",
                "contact_email": "jordan.lee@university.edu",
                "contact_phone": "+1-555-0103",
                "status": "ACTIVE",
            },
            {
                "id": "rep-staging-watch-found",
                "owner_id": users["alex.chen@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "FOUND",
                "item_name": "Black Digital Smartwatch Found near Gym Benches",
                "category": "JEWELRY_WATCHES",
                "description": "Found a 45mm black Apple smartwatch left on workout bench at athletic pavilion.",
                "event_date": today - timedelta(days=3),
                "location_text": "Athletic Pavilion Rec Center",
                "latitude": 37.7731,
                "longitude": -122.4202,
                "contact_name": "Alex Chen",
                "contact_email": "alex.chen@university.edu",
                "contact_phone": "+1-555-0101",
                "status": "ACTIVE",
            },

            # Pair 12: Kanken Backpack
            {
                "id": "rep-staging-backpack-lost",
                "owner_id": users["alex.chen@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "Forest Green Fjallraven Kanken Classic Backpack",
                "category": "BAGS_WALLETS",
                "description": "Green canvas backpack with red round fox logo, containing notebook and pencil case.",
                "event_date": today - timedelta(days=2),
                "location_text": "Student Union Cafeteria Food Court",
                "latitude": 37.7760,
                "longitude": -122.4180,
                "contact_name": "Alex Chen",
                "contact_email": "alex.chen@university.edu",
                "contact_phone": "+1-555-0101",
                "status": "ACTIVE",
            },
            {
                "id": "rep-staging-backpack-found",
                "owner_id": users["maya.patel@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "FOUND",
                "item_name": "Green Swedish Canvas Backpack with Notebooks",
                "category": "BAGS_WALLETS",
                "description": "Green square backpack left under cafeteria table during lunchtime.",
                "event_date": today - timedelta(days=2),
                "location_text": "Student Union Food Court",
                "latitude": 37.7761,
                "longitude": -122.4179,
                "contact_name": "Maya Patel",
                "contact_email": "maya.patel@university.edu",
                "contact_phone": "+1-555-0102",
                "status": "ACTIVE",
            },

            # Resolved Report 1
            {
                "id": "rep-staging-jacket-resolved",
                "owner_id": users["alex.chen@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "Black North Face Puffer Jacket",
                "category": "CLOTHING",
                "description": "Left on coat rack in Student Center. Successfully returned!",
                "event_date": today - timedelta(days=10),
                "location_text": "Student Center",
                "latitude": 37.7760,
                "longitude": -122.4180,
                "contact_name": "Alex Chen",
                "contact_email": "alex.chen@university.edu",
                "contact_phone": "+1-555-0101",
                "status": "RESOLVED",
            },

            # Resolved Report 2
            {
                "id": "rep-staging-airpods-resolved",
                "owner_id": users["jordan.lee@university.edu"].id,
                "community_id": "comm-central-campus",
                "type": "LOST",
                "item_name": "AirPods Pro 2nd Gen with Charging Case",
                "category": "ELECTRONICS",
                "description": "Found on library 1st floor. Verified serial number and returned to owner.",
                "event_date": today - timedelta(days=12),
                "location_text": "Main Library",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "contact_name": "Jordan Lee",
                "contact_email": "jordan.lee@university.edu",
                "contact_phone": "+1-555-0103",
                "status": "RESOLVED",
            },

            # Flagged/Spam Report for Admin Moderation Demo
            {
                "id": "rep-staging-spam-report",
                "owner_id": users["spammer@sketchy.io"].id,
                "community_id": "comm-central-campus",
                "type": "FOUND",
                "item_name": "FREE iPhone Giveaway click bit.ly/spam",
                "category": "ELECTRONICS",
                "description": "Win a brand new free smartphone click here to claim your reward immediately!!",
                "event_date": today,
                "location_text": "Campus Wide",
                "latitude": 37.7750,
                "longitude": -122.4190,
                "contact_name": "Free Phones",
                "contact_email": "spammer@sketchy.io",
                "contact_phone": "+1-555-9999",
                "status": "ACTIVE",
            },
        ]

        for rd in reports_data:
            existing = db.query(Report).filter(Report.id == rd["id"]).first()
            if not existing:
                rd_copy = dict(rd)
                rd_copy["normalized_location"] = normalize_location(rd_copy["location_text"])
                rep = Report(**rd_copy)
                db.add(rep)

        db.commit()

        # 5. Seed Contact Request (Maya contacting Alex regarding MacBook)
        mbp_report = db.query(Report).filter(Report.id == "rep-staging-mbp-lost").first()
        if mbp_report:
            existing_cr = db.query(ContactRequest).filter(
                ContactRequest.report_id == mbp_report.id,
                ContactRequest.requester_email == "maya.patel@university.edu",
            ).first()
            if not existing_cr:
                cr = ContactRequest(
                    report_id=mbp_report.id,
                    requester_id=users["maya.patel@university.edu"].id,
                    requester_name="Maya Patel",
                    requester_email="maya.patel@university.edu",
                    requester_phone="+1-555-0102",
                    message="Hi Alex! I believe I found your laptop at the circulation desk on the 2nd floor.",
                    status="PENDING",
                )
                db.add(cr)

        # 6. Seed Abuse Flag (Flag on the spam report)
        spam_rep = db.query(Report).filter(Report.id == "rep-staging-spam-report").first()
        if spam_rep:
            existing_flag = db.query(ReportFlag).filter(ReportFlag.report_id == spam_rep.id).first()
            if not existing_flag:
                flag = ReportFlag(
                    report_id=spam_rep.id,
                    reporter_id=users["alex.chen@university.edu"].id,
                    reason="Commercial spam and phishing link posted as a lost item.",
                    status="OPEN",
                )
                db.add(flag)

        db.commit()

        # 7. Warm in-memory matching index
        indexed_count = ReportService.rebuild_all_indexes(db)
        print(f"[LostLink Staging Seed] Successfully rebuilt in-memory index with {indexed_count} active reports.")

        print("\n========================================================")
        print(" LostLink Staging Environment Ready!")
        print("========================================================")
        print(" Demo Accounts:")
        print("   - Admin:    admin@lostlink.org       / Admin123!   (Role: ADMIN)")
        print("   - Student:  alex.chen@university.edu / Student123! (Role: USER)")
        print("   - Student:  maya.patel@university.edu/ Student123! (Role: USER)")
        print("   - Student:  jordan.lee@university.edu/ Student123! (Role: USER)")
        print(" Communities: 'central-campus', 'tech-park'")
        print(" Features primed: High-confidence pairs, open abuse flags, contact requests.")
        print("========================================================\n")

    finally:
        db.close()


if __name__ == "__main__":
    seed_staging()
