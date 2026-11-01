"""
Tests for Phase 7:
- Double-blind contact flow (masked until accepted)
- Ownership authorization on accept/decline
- Security headers middleware
- Admin moderation endpoints
- DPDP / GDPR Account deletion and data scrub flow
"""
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.report import Report, ContactRequest, ReportFlag, User, RefreshToken
from app.services.auth_service import get_current_user


def test_security_headers_present(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in res.headers["content-security-policy"]


def test_contact_request_double_blind_flow(client: TestClient, db_session):
    # Setup Owner, Requester, Stranger
    owner = User(display_name="Owner Alice", email="alice@test.org", password_hash="hash", role="user")
    requester = User(display_name="Requester Bob", email="bob.secret@test.org", password_hash="hash", role="user")
    stranger = User(display_name="Stranger Charlie", email="charlie@test.org", password_hash="hash", role="user")
    db_session.add_all([owner, requester, stranger])
    db_session.commit()
    for u in (owner, requester, stranger):
        db_session.refresh(u)

    # Owner files report
    report = Report(
        type="LOST",
        item_name="Silver Laptop",
        category="ELECTRONICS",
        description="MacBook Pro left in library.",
        event_date=date(2026, 10, 20),
        location_text="Main Library",
        normalized_location="main library",
        status="ACTIVE",
        owner_id=owner.id,
        contact_name="Alice Owner",
        contact_email="alice@test.org",
        contact_phone="555-0199",
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    # 1. Requester Bob submits contact request
    app.dependency_overrides[get_current_user] = lambda: requester
    res_req = client.post("/api/contact-requests", json={
        "report_id": report.id,
        "requester_name": "Bob Requester",
        "requester_email": "bob.secret@test.org",
        "requester_phone": "555-9876",
        "message": "I found a silver MacBook matching your description at the front desk.",
    })
    assert res_req.status_code == 201
    req_id = res_req.json()["data"]["id"]
    # Email is masked in creation response
    assert "b***t@test.org" in res_req.json()["data"]["requester_email"]

    # 3. Owner views incoming requests — email is masked while PENDING
    app.dependency_overrides[get_current_user] = lambda: owner
    res_rec = client.get("/api/contact-requests/received")
    assert res_rec.status_code == 200
    incoming = res_rec.json()["data"]
    assert len(incoming) >= 1
    target_req = next(r for r in incoming if r["id"] == req_id)
    assert target_req["status"] == "PENDING"
    assert "b***t@test.org" in target_req["requester_email"]

    # 4. Stranger cannot accept or decline request
    app.dependency_overrides[get_current_user] = lambda: stranger
    res_stranger = client.post(f"/api/contact-requests/{req_id}/accept", json={"owner_notes": "Hi"})
    assert res_stranger.status_code == 403

    # 5. Owner accepts contact request — email and phone are officially unmasked
    app.dependency_overrides[get_current_user] = lambda: owner
    res_accept = client.post(f"/api/contact-requests/{req_id}/accept", json={"owner_notes": "Thank you, please email me."})
    assert res_accept.status_code == 200
    accepted_data = res_accept.json()["data"]
    assert accepted_data["status"] == "ACCEPTED"
    assert accepted_data["requester_email"] == "bob.secret@test.org"
    assert accepted_data["requester_phone"] == "555-9876"

    # Clean up auth override
    app.dependency_overrides.pop(get_current_user, None)


def test_admin_moderation_endpoints(client: TestClient, db_session):
    admin = User(display_name="Admin Chief", email="admin@test.org", password_hash="hash", role="admin")
    regular = User(display_name="Regular Joe", email="joe@test.org", password_hash="hash", role="user")
    db_session.add_all([admin, regular])
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(regular)

    report = Report(
        type="LOST",
        item_name="Spam Report",
        category="OTHER",
        description="Spam link here",
        event_date=date(2026, 10, 20),
        location_text="Online",
        normalized_location="online",
        status="ACTIVE",
        contact_name="Spammer",
        contact_email="spam@test.org",
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    # Flag report
    client.post(f"/api/reports/{report.id}/flag", json={"reason": "Inappropriate spam content"})

    # Regular user cannot access admin flags
    app.dependency_overrides[get_current_user] = lambda: regular
    assert client.get("/api/admin/flags").status_code == 403

    # Admin can access flags
    app.dependency_overrides[get_current_user] = lambda: admin
    res_flags = client.get("/api/admin/flags")
    assert res_flags.status_code == 200
    flags = res_flags.json()["data"]
    assert len(flags) >= 1

    # Admin hides the report
    res_mod = client.patch(f"/api/admin/reports/{report.id}/status", json={"status": "HIDDEN"})
    assert res_mod.status_code == 200
    assert res_mod.json()["data"]["status"] == "HIDDEN"

    # Report is now hidden from active index
    db_session.refresh(report)
    assert report.status == "HIDDEN"

    app.dependency_overrides.pop(get_current_user, None)


def test_dpdp_gdpr_delete_my_account(client: TestClient, db_session):
    user_to_delete = User(
        display_name="Departing User",
        email="departing@example.com",
        password_hash="hash",
        role="user",
        is_active=True,
    )
    db_session.add(user_to_delete)
    db_session.commit()
    db_session.refresh(user_to_delete)

    report = Report(
        type="LOST",
        item_name="Keys",
        category="KEYS_CARDS",
        description="House keys on red ring",
        event_date=date(2026, 10, 21),
        location_text="Cafeteria",
        normalized_location="cafeteria",
        status="ACTIVE",
        owner_id=user_to_delete.id,
        contact_name="Departing User",
        contact_email="departing@example.com",
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    # Call DELETE /api/auth/me
    app.dependency_overrides[get_current_user] = lambda: user_to_delete
    res = client.delete("/api/auth/me")
    assert res.status_code == 200
    assert "permanently anonymized" in res.json()["data"]["message"]

    # Verify user record is scrubbed
    db_session.refresh(user_to_delete)
    assert user_to_delete.is_active is False
    assert user_to_delete.display_name == "Deleted User"
    assert "deleted_" in user_to_delete.email

    # Verify report contact info is scrubbed
    db_session.refresh(report)
    assert report.contact_name == "Deleted User"
    assert report.contact_email == "deleted@anonymized.lostlink"

    app.dependency_overrides.pop(get_current_user, None)

