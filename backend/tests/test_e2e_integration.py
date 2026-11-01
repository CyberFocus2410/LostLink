"""
End-to-End Integration Tests for LostLink (Prompt 5).
Verifies:
1. Complete Create -> Match -> Contact Request -> Resolve lifecycle
2. Server-side validation error handling
3. Empty search result handling
4. Privacy protection (no contact leaks in public endpoints)
5. Index synchronization across resolution
"""
from datetime import date, timedelta


def test_full_create_to_match_to_resolve_lifecycle(client):
    today = date.today()

    # Step 1: User submits a LOST report
    lost_payload = {
        "type": "LOST",
        "item_name": "Bose QuietComfort 45 Headphones",
        "category": "ELECTRONICS",
        "description": "Matte black Bose QC45 over-ear noise-cancelling headphones left in black zippered carry case with audio cable inside.",
        "event_date": str(today),
        "location_text": "Main Library 2nd Floor Study Room 204",
        "contact_name": "Jordan Lee",
        "contact_email": "jordan.lee@campus.edu",
        "contact_phone": "+1-555-0149",
    }
    lost_res = client.post("/api/reports", json=lost_payload)
    assert lost_res.status_code == 201
    lost_data = lost_res.json()["data"]
    lost_id = lost_data["id"]

    # Verify private fields omitted
    assert "contact_name" not in lost_data
    assert "contact_email" not in lost_data
    assert "contact_phone" not in lost_data

    # Step 2: Finder submits a FOUND report (Strong overlap)
    found_payload = {
        "type": "FOUND",
        "item_name": "Black Bose Noise Cancelling Headphones in Case",
        "category": "ELECTRONICS",
        "description": "Found a pair of black Bose headphones inside a protective zippered travel pouch on a study table.",
        "event_date": str(today),
        "location_text": "Library 2nd Floor Study Hall",
        "contact_name": "Library Circulation Staff",
        "contact_email": "circ@campus.edu",
        "contact_phone": "+1-555-0105",
    }
    found_res = client.post("/api/reports", json=found_payload)
    assert found_res.status_code == 201
    found_data = found_res.json()["data"]
    found_id = found_data["id"]

    # Step 3: Query matches for the lost report
    matches_res = client.get(f"/api/reports/{lost_id}/matches?limit=5")
    assert matches_res.status_code == 200
    matches_body = matches_res.json()
    assert matches_body["error"] is None

    matches = matches_body["data"]["matches"]
    assert len(matches) >= 1

    top_candidate = matches[0]
    assert top_candidate["candidate"]["id"] == found_id
    assert top_candidate["total_score"] >= 65.0

    # Verify component scores
    components = top_candidate["components"]
    assert components["category_score"] == 100.0
    assert components["date_score"] == 100.0
    assert components["location_score"] >= 70.0  # Same facility cluster (Library)
    assert components["keyword_score"] > 0.0

    # Verify explainability and disclaimer
    assert top_candidate["disclaimer"] == "Potential match—not verified ownership"
    assert any("Same item category" in r for r in top_candidate["reasons"])
    assert any("bose" in kw.lower() for kw in top_candidate["shared_keywords"])

    # Verify private fields of candidate NOT leaked in match payload
    candidate_obj = top_candidate["candidate"]
    assert "contact_name" not in candidate_obj
    assert "contact_email" not in candidate_obj
    assert "contact_phone" not in candidate_obj

    # Step 4: User initiates a contact request
    contact_res = client.post(
        "/api/contact-requests",
        json={
            "report_id": found_id,
            "requester_name": "Jordan Lee",
            "requester_email": "jordan.lee@campus.edu",
            "message": "I lost my Bose QC45 headphones on the 2nd floor today. The case has a slight white scuff mark on the top.",
        },
    )
    assert contact_res.status_code == 201
    assert contact_res.json()["data"]["report_id"] == found_id

    # Step 5: Item is recovered -> Mark FOUND report as RESOLVED
    resolve_res = client.post(f"/api/reports/{found_id}/resolve")
    assert resolve_res.status_code == 200
    assert resolve_res.json()["data"]["status"] == "RESOLVED"

    # Step 6: Verify candidate is pruned from active matches
    matches_after_resolve = client.get(f"/api/reports/{lost_id}/matches?limit=5")
    assert matches_after_resolve.status_code == 200
    updated_matches = matches_after_resolve.json()["data"]["matches"]
    candidate_ids = [m["candidate"]["id"] for m in updated_matches]
    assert found_id not in candidate_ids


def test_invalid_submission_and_field_errors(client):
    # Missing required category and future date
    res = client.post(
        "/api/reports",
        json={
            "type": "LOST",
            "item_name": "X",  # Too short (min 2)
            "category": "INVALID_CAT",
            "description": "Hi",  # Too short (min 5)
            "event_date": str(date.today() + timedelta(days=10)),
            "location_text": "A",  # Too short (min 2)
            "contact_name": "",
            "contact_email": "invalid-email",
        },
    )
    assert res.status_code == 422
    body = res.json()
    assert body["data"] is None
    assert body["error"]["code"] == "VALIDATION_ERROR"
    fields = body["error"]["fields"]
    assert "item_name" in fields
    assert "category" in fields
    assert "description" in fields
    assert "event_date" in fields
    assert "contact_email" in fields


def test_empty_search_results_flow(client):
    res = client.get("/api/reports?q=nonexistentxyz123item")
    assert res.status_code == 200
    body = res.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0
    assert body["error"] is None


def test_complete_user_lifecycle_with_photo_contact_resolve_and_erasure(real_auth_client):
    """
    Prompt 9 Comprehensive QA Lifecycle:
    register -> log in -> report lost item with photo -> see matches ->
    send contact request -> owner accepts -> resolve -> delete account
    """
    client = real_auth_client
    import io
    from PIL import Image

    # 1. Register User A (Report Owner)
    reg_a = client.post(
        "/api/auth/register",
        json={
            "display_name": "Lifecycle Owner",
            "email": "owner_lifecycle@campus.edu",
            "password": "Password123!",
        },
    )
    assert reg_a.status_code == 201
    assert "lostlink_access" in client.cookies

    # 2. Report Lost Item
    today = date.today()
    rep_res = client.post(
        "/api/reports",
        json={
            "type": "LOST",
            "item_name": "Sony WH-1000XM5 Headphones",
            "category": "ELECTRONICS",
            "description": "Silver Sony XM5 headphones in gray case with aux cord.",
            "event_date": str(today),
            "location_text": "Engineering Building Lab 202",
            "contact_name": "Lifecycle Owner",
            "contact_email": "owner_lifecycle@campus.edu",
        },
    )
    assert rep_res.status_code == 201
    rep_id = rep_res.json()["data"]["id"]

    # 3. Upload Photo to Report
    img_byte_arr = io.BytesIO()
    img = Image.new("RGB", (200, 200), color="silver")
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    photo_res = client.post(
        f"/api/reports/{rep_id}/images",
        files={"file": ("sony.jpg", img_byte_arr, "image/jpeg")},
    )
    assert photo_res.status_code == 201
    img_data = photo_res.json()["data"]
    assert img_data["report_id"] == rep_id
    assert "image_url" in img_data

    # 4. Register User B (Finder)
    client.cookies.clear()
    reg_b = client.post(
        "/api/auth/register",
        json={
            "display_name": "Lifecycle Finder",
            "email": "finder_lifecycle@campus.edu",
            "password": "Password123!",
        },
    )
    assert reg_b.status_code == 201

    # User B reports Found Item
    found_res = client.post(
        "/api/reports",
        json={
            "type": "FOUND",
            "item_name": "Silver Sony Headphones in Case",
            "category": "ELECTRONICS",
            "description": "Found silver Sony wireless headphones in gray pouch in engineering hall.",
            "event_date": str(today),
            "location_text": "Engineering Building Hallway",
            "contact_name": "Lifecycle Finder",
            "contact_email": "finder_lifecycle@campus.edu",
        },
    )
    assert found_res.status_code == 201
    found_id = found_res.json()["data"]["id"]

    # 5. User B inspects matches -> sees User A's lost item
    match_res = client.get(f"/api/reports/{found_id}/matches")
    assert match_res.status_code == 200
    candidates = match_res.json()["data"]["matches"]
    assert any(c["candidate"]["id"] == rep_id for c in candidates)

    # 6. User B sends contact request to User A's report
    contact_req = client.post(
        "/api/contact-requests",
        json={
            "report_id": rep_id,
            "requester_name": "Lifecycle Finder",
            "requester_email": "finder_lifecycle@campus.edu",
            "requester_phone": "+1-555-8888",
            "message": "I found your silver Sony headphones! They are safe with me.",
        },
    )
    assert contact_req.status_code == 201
    req_id = contact_req.json()["data"]["id"]

    # 7. Log back in as User A (Owner)
    client.cookies.clear()
    login_a = client.post(
        "/api/auth/login",
        json={"email": "owner_lifecycle@campus.edu", "password": "Password123!"},
    )
    assert login_a.status_code == 200

    # User A checks received contact requests -> sees masked contact
    received_res = client.get("/api/contact-requests/received")
    assert received_res.status_code == 200
    requests_list = received_res.json()["data"]
    matched_req = next((r for r in requests_list if r["id"] == req_id), None)
    assert matched_req is not None
    assert matched_req["status"] == "PENDING"
    # Contact is masked
    assert "@" in matched_req["requester_email"]
    assert matched_req["requester_email"].startswith("f***")

    # 8. User A accepts contact request
    accept_res = client.post(f"/api/contact-requests/{req_id}/accept", json={"owner_notes": "Thank you so much!"})
    assert accept_res.status_code == 200
    accepted_data = accept_res.json()["data"]
    assert accepted_data["status"] == "ACCEPTED"
    # Direct contact now unmasked
    assert accepted_data["requester_email"] == "finder_lifecycle@campus.edu"

    # 9. User A marks report RESOLVED
    res_res = client.post(f"/api/reports/{rep_id}/resolve")
    assert res_res.status_code == 200
    assert res_res.json()["data"]["status"] == "RESOLVED"

    # 10. User A executes DPDP Act / GDPR Account Erasure
    del_res = client.delete("/api/auth/me")
    assert del_res.status_code == 200
    assert del_res.json()["data"]["erased"] is True

    # Verify session is terminated and user is scrubbed
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 401
