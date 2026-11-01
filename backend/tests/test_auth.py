"""
Auth endpoint tests: register, login, me, refresh, logout.
These tests spin up a real in-memory DB (no auth override) to exercise the full auth flow.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.matching.index import matching_index
from app.limiter import limiter

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(scope="function")
def auth_client():
    """Client with real DB but NO dependency overrides — full auth flow."""
    Base.metadata.create_all(bind=_engine)
    matching_index.clear()
    limiter.reset()

    def override_db():
        s = _TestingSession()
        try:
            yield s
        finally:
            s.close()

    # Override only the DB — NOT get_current_user
    app.dependency_overrides[get_db] = override_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=_engine)
    matching_index.clear()


_VALID_USER = {
    "display_name": "Alice Test",
    "email": "alice@example.com",
    "password": "Secure1234",
}


def test_register_success(auth_client):
    res = auth_client.post("/api/auth/register", json=_VALID_USER)
    assert res.status_code == 201
    body = res.json()
    assert body["error"] is None
    user = body["data"]
    assert user["email"] == "alice@example.com"
    assert user["display_name"] == "Alice Test"
    assert "password_hash" not in user  # never leaked
    # Cookies should be set
    assert "lostlink_access" in res.cookies
    assert "lostlink_refresh" in res.cookies


def test_register_duplicate_email(auth_client):
    auth_client.post("/api/auth/register", json=_VALID_USER)
    res = auth_client.post("/api/auth/register", json=_VALID_USER)
    assert res.status_code == 409


def test_register_weak_password(auth_client):
    res = auth_client.post("/api/auth/register", json={**_VALID_USER, "password": "short"})
    assert res.status_code == 422


def test_register_password_no_digit(auth_client):
    res = auth_client.post("/api/auth/register", json={**_VALID_USER, "password": "NoDigitsHere"})
    assert res.status_code == 422


def test_login_success(auth_client):
    auth_client.post("/api/auth/register", json=_VALID_USER)
    res = auth_client.post("/api/auth/login", json={"email": _VALID_USER["email"], "password": _VALID_USER["password"]})
    assert res.status_code == 200
    assert "lostlink_access" in res.cookies


def test_login_wrong_password(auth_client):
    auth_client.post("/api/auth/register", json=_VALID_USER)
    res = auth_client.post("/api/auth/login", json={"email": _VALID_USER["email"], "password": "WrongPass99"})
    assert res.status_code == 401
    # Generic message — doesn't reveal user exists
    assert "credentials" in res.json()["error"]["message"].lower()


def test_login_unknown_email(auth_client):
    res = auth_client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "AnyPass123"})
    assert res.status_code == 401


def test_me_authenticated(auth_client):
    auth_client.post("/api/auth/register", json=_VALID_USER)
    res = auth_client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["data"]["email"] == "alice@example.com"


def test_me_unauthenticated(auth_client):
    res = auth_client.get("/api/auth/me")
    assert res.status_code == 401


def test_protected_create_report_requires_auth(auth_client):
    """POST /api/reports must return 401 when not logged in."""
    payload = {
        "type": "LOST",
        "item_name": "Test Laptop",
        "category": "ELECTRONICS",
        "description": "Silver laptop left at library",
        "event_date": "2026-10-30",
        "location_text": "Main Library",
        "contact_name": "Test User",
        "contact_email": "test@example.com",
    }
    res = auth_client.post("/api/reports", json=payload)
    assert res.status_code == 401


def test_create_report_after_login(auth_client):
    """Authenticated user can create a report."""
    auth_client.post("/api/auth/register", json=_VALID_USER)
    payload = {
        "type": "LOST",
        "item_name": "Silver Laptop",
        "category": "ELECTRONICS",
        "description": "Silver laptop with blue sticker found near library",
        "event_date": "2026-10-30",
        "location_text": "Main Library",
        "contact_name": "Alice Test",
        "contact_email": "alice@example.com",
    }
    res = auth_client.post("/api/reports", json=payload)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["item_name"] == "Silver Laptop"
    assert "contact_email" not in data  # privacy guard


def test_logout_revokes_refresh(auth_client):
    auth_client.post("/api/auth/register", json=_VALID_USER)
    # Logout
    res_logout = auth_client.post("/api/auth/logout")
    assert res_logout.status_code == 200
    # After logout, /me should be 401
    res_me = auth_client.get("/api/auth/me")
    assert res_me.status_code == 401


def test_refresh_rotates_token(auth_client):
    auth_client.post("/api/auth/register", json=_VALID_USER)
    old_access = auth_client.cookies.get("lostlink_access")
    old_refresh = auth_client.cookies.get("lostlink_refresh")
    res = auth_client.post("/api/auth/refresh")
    assert res.status_code == 200
    new_access = auth_client.cookies.get("lostlink_access")
    new_refresh = auth_client.cookies.get("lostlink_refresh")
    assert new_access != old_access  # access token was re-issued
    assert new_refresh != old_refresh  # refresh token was rotated


def test_user_cannot_edit_or_resolve_others_report(auth_client):
    # Register User A and create report
    auth_client.post("/api/auth/register", json=_VALID_USER)
    payload = {
        "type": "LOST",
        "item_name": "Alice's Calculator",
        "category": "ELECTRONICS",
        "description": "TI-84 Plus CE graphing calculator left in lecture hall",
        "event_date": "2026-10-31",
        "location_text": "Hall 101",
        "contact_name": "Alice",
        "contact_email": "alice@example.com",
    }
    create_res = auth_client.post("/api/reports", json=payload)
    assert create_res.status_code == 201
    report_id = create_res.json()["data"]["id"]

    # Register User B (automatically switches cookies)
    user_b = {
        "display_name": "Bob Test",
        "email": "bob@example.com",
        "password": "Password1234",
    }
    auth_client.post("/api/auth/register", json=user_b)

    # User B attempts to edit User A's report -> 403 Forbidden
    patch_res = auth_client.patch(f"/api/reports/{report_id}", json={"item_name": "Hacked Title"})
    assert patch_res.status_code == 403
    assert "permission" in patch_res.json()["error"]["message"].lower()

    # User B attempts to resolve User A's report -> 403 Forbidden
    resolve_res = auth_client.post(f"/api/reports/{report_id}/resolve")
    assert resolve_res.status_code == 403
    assert "permission" in resolve_res.json()["error"]["message"].lower()


def test_my_reports_filtered_to_logged_in_user(auth_client):
    # Register User A and create report
    auth_client.post("/api/auth/register", json=_VALID_USER)
    auth_client.post(
        "/api/reports",
        json={
            "type": "LOST",
            "item_name": "Alice's Keys",
            "category": "KEYS_CARDS",
            "description": "Keychain with 3 brass keys",
            "event_date": "2026-10-31",
            "location_text": "Library",
            "contact_name": "Alice",
            "contact_email": "alice@example.com",
        },
    )

    # Check /api/reports/mine for User A
    res_a = auth_client.get("/api/reports/mine")
    assert res_a.status_code == 200
    assert len(res_a.json()["data"]) == 1
    assert res_a.json()["data"][0]["item_name"] == "Alice's Keys"

    # Register User B
    auth_client.post(
        "/api/auth/register",
        json={
            "display_name": "Bob Test",
            "email": "bob@example.com",
            "password": "Password1234",
        },
    )

    # Check /api/reports/mine for User B -> should have 0 reports
    res_b = auth_client.get("/api/reports/mine")
    assert res_b.status_code == 200
    assert len(res_b.json()["data"]) == 0


def test_csrf_origin_check_blocks_untrusted_origin(auth_client):
    auth_client.post("/api/auth/register", json=_VALID_USER)
    # Mutating request with untrusted origin
    headers = {"Origin": "https://malicious-site.attacker.com"}
    res = auth_client.post(
        "/api/reports",
        json={
            "type": "LOST",
            "item_name": "Should Be Blocked",
            "category": "ELECTRONICS",
            "description": "Test CSRF protection",
            "event_date": "2026-10-31",
            "location_text": "Nowhere",
            "contact_name": "Tester",
            "contact_email": "tester@example.com",
        },
        headers=headers,
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "CSRF_FORBIDDEN"


def test_forgot_password_generic_response(auth_client):
    # Should always succeed and never leak if email exists
    res1 = auth_client.post("/api/auth/forgot-password", json={"email": "alice@example.com"})
    assert res1.status_code == 200
    res2 = auth_client.post("/api/auth/forgot-password", json={"email": "nonexistent@example.com"})
    assert res2.status_code == 200


def test_login_rate_limiting(auth_client):
    # Limit is 20 per minute. Exceeding it returns 429.
    for _ in range(20):
        auth_client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "WrongPassword1"})
    res = auth_client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "WrongPassword1"})
    assert res.status_code == 429
