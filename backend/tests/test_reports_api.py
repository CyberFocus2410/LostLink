"""
Integration tests for reports API, validations, filters, edits, and privacy rules.
"""
from datetime import date, timedelta


def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["data"]["status"] == "healthy"
    assert json_data["error"] is None


def test_create_valid_report(client):
    payload = {
        "type": "LOST",
        "item_name": "Blue Anker Power Bank",
        "category": "ELECTRONICS",
        "description": "Lost my 10000mAh blue Anker portable charger with a short USB-C braided cable.",
        "event_date": str(date.today()),
        "location_text": "Engineering Hall Room 101",
        "contact_name": "Devin Cole",
        "contact_email": "devin.cole@campus.edu",
        "contact_phone": "+1-555-0133",
    }
    res = client.post("/api/reports", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["error"] is None
    data = body["data"]

    assert data["item_name"] == "Blue Anker Power Bank"
    assert data["category"] == "ELECTRONICS"
    assert data["status"] == "ACTIVE"
    assert "id" in data
    assert len(data["id"]) > 10

    # Privacy verification: private contact info MUST NOT appear in public output
    assert "contact_name" not in data
    assert "contact_email" not in data
    assert "contact_phone" not in data


def test_create_report_invalid_inputs(client):
    # 1. Invalid Category
    res = client.post(
        "/api/reports",
        json={
            "type": "LOST",
            "item_name": "Calculator",
            "category": "SPORTS_EQUIPMENT",  # Invalid enum
            "description": "Scientific calculator left in hall.",
            "event_date": str(date.today()),
            "location_text": "Hall B",
            "contact_name": "Test User",
            "contact_email": "test@campus.edu",
        },
    )
    assert res.status_code == 422
    err_body = res.json()
    assert err_body["error"]["code"] == "VALIDATION_ERROR"
    assert "category" in err_body["error"]["fields"]

    # 2. Future Date
    future_date = date.today() + timedelta(days=5)
    res_date = client.post(
        "/api/reports",
        json={
            "type": "FOUND",
            "item_name": "Water Bottle",
            "category": "OTHER",
            "description": "Metal flask left on stairs.",
            "event_date": str(future_date),
            "location_text": "Main Stairwell",
            "contact_name": "Test User",
            "contact_email": "test@campus.edu",
        },
    )
    assert res_date.status_code == 422
    assert "event_date" in res_date.json()["error"]["fields"]

    # 3. Invalid Email Format
    res_email = client.post(
        "/api/reports",
        json={
            "type": "LOST",
            "item_name": "Water Bottle",
            "category": "OTHER",
            "description": "Metal flask left on stairs.",
            "event_date": str(date.today()),
            "location_text": "Main Stairwell",
            "contact_name": "Test User",
            "contact_email": "not-an-email",
        },
    )
    assert res_email.status_code == 422
    assert "contact_email" in res_email.json()["error"]["fields"]


def test_list_reports_filtering(client):
    # Seed 3 reports
    today = date.today()
    client.post(
        "/api/reports",
        json={
            "type": "LOST",
            "item_name": "Dell XPS 13 Laptop",
            "category": "ELECTRONICS",
            "description": "Silver ultrabook laptop with silver bezel.",
            "event_date": str(today),
            "location_text": "Library 1st Floor",
            "contact_name": "Alice",
            "contact_email": "alice@campus.edu",
        },
    )
    client.post(
        "/api/reports",
        json={
            "type": "FOUND",
            "item_name": "Red Backpack with Notebooks",
            "category": "BAGS_WALLETS",
            "description": "Jansport red backpack with math notebooks inside.",
            "event_date": str(today - timedelta(days=2)),
            "location_text": "Student Center",
            "contact_name": "Bob",
            "contact_email": "bob@campus.edu",
        },
    )
    client.post(
        "/api/reports",
        json={
            "type": "FOUND",
            "item_name": "Dorm Room Keycard",
            "category": "KEYS_CARDS",
            "description": "Campus RFID dorm access card with sticker.",
            "event_date": str(today - timedelta(days=4)),
            "location_text": "Dining Hall",
            "contact_name": "Staff",
            "contact_email": "staff@campus.edu",
        },
    )

    # Filter by type: FOUND
    res_found = client.get("/api/reports?type=FOUND")
    assert res_found.status_code == 200
    assert len(res_found.json()["data"]) == 2

    # Filter by category: ELECTRONICS
    res_elec = client.get("/api/reports?category=ELECTRONICS")
    assert res_elec.status_code == 200
    assert len(res_elec.json()["data"]) == 1
    assert res_elec.json()["data"][0]["item_name"] == "Dell XPS 13 Laptop"

    # Search keyword: "backpack"
    res_search = client.get("/api/reports?q=backpack")
    assert res_search.status_code == 200
    assert len(res_search.json()["data"]) == 1
    assert res_search.json()["data"][0]["item_name"] == "Red Backpack with Notebooks"


def test_get_report_by_id_and_not_found(client):
    today = date.today()
    create_res = client.post(
        "/api/reports",
        json={
            "type": "LOST",
            "item_name": "Casio Watch",
            "category": "JEWELRY_WATCHES",
            "description": "Black resin digital watch.",
            "event_date": str(today),
            "location_text": "Gym Lockers",
            "contact_name": "Charlie",
            "contact_email": "charlie@campus.edu",
        },
    )
    report_id = create_res.json()["data"]["id"]

    # Valid GET
    res = client.get(f"/api/reports/{report_id}")
    assert res.status_code == 200
    assert res.json()["data"]["id"] == report_id

    # Non-existent GET
    res_404 = client.get("/api/reports/non-existent-uuid-12345")
    assert res_404.status_code == 404
    assert res_404.json()["error"]["code"] == "NOT_FOUND"


def test_update_and_resolve_report(client):
    today = date.today()
    create_res = client.post(
        "/api/reports",
        json={
            "type": "LOST",
            "item_name": "Black Umbrella",
            "category": "OTHER",
            "description": "Compact black folding umbrella with wooden handle.",
            "event_date": str(today),
            "location_text": "Campus Cafe",
            "contact_name": "Dana",
            "contact_email": "dana@campus.edu",
        },
    )
    report_id = create_res.json()["data"]["id"]

    # Update description & item_name
    patch_res = client.patch(
        f"/api/reports/{report_id}",
        json={"item_name": "Black ShedRain Umbrella", "description": "Updated detailed description of the umbrella."},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["item_name"] == "Black ShedRain Umbrella"

    # Resolve report
    resolve_res = client.post(f"/api/reports/{report_id}/resolve")
    assert resolve_res.status_code == 200
    assert resolve_res.json()["data"]["status"] == "RESOLVED"

    # Confirm status persisted
    get_res = client.get(f"/api/reports/{report_id}")
    assert get_res.json()["data"]["status"] == "RESOLVED"


def test_contact_request_and_flag(client):
    today = date.today()
    create_res = client.post(
        "/api/reports",
        json={
            "type": "FOUND",
            "item_name": "Silver Ring",
            "category": "JEWELRY_WATCHES",
            "description": "Silver band ring found near water fountain.",
            "event_date": str(today),
            "location_text": "Quad Walkway",
            "contact_name": "Eve",
            "contact_email": "eve@campus.edu",
        },
    )
    report_id = create_res.json()["data"]["id"]

    # Contact request
    contact_res = client.post(
        "/api/contact-requests",
        json={
            "report_id": report_id,
            "requester_name": "Potential Owner",
            "requester_email": "owner@campus.edu",
            "message": "I believe this silver ring might be mine. It has an engraving inside.",
        },
    )
    assert contact_res.status_code == 201
    assert contact_res.json()["data"]["report_id"] == report_id
    assert contact_res.json()["data"]["status"] == "PENDING"

    # Flag report
    flag_res = client.post(
        f"/api/reports/{report_id}/flag",
        json={"reason": "Contains inaccurate location information."},
    )
    assert flag_res.status_code == 201
    assert flag_res.json()["data"]["report_id"] == report_id
