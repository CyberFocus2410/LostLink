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
