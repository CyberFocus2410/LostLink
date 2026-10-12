"""
Tests for matching endpoint: scoring, opposite-type filtering, resolution exclusion, and explanations.
"""
from datetime import date, timedelta


def test_matches_opposite_type_and_components(client):
    today = date.today()

    # Create Lost Report
    lost_res = client.post(
        "/api/reports",
        json={
            "type": "LOST",
            "item_name": "Apple iPad Air 5th Gen Blue",
            "category": "ELECTRONICS",
            "description": "Blue iPad Air with white apple pencil magnetic attachment. Left on bench.",
            "event_date": str(today),
            "location_text": "Main Library 2nd Floor",
            "contact_name": "Owner",
            "contact_email": "owner@campus.edu",
        },
    )
    lost_id = lost_res.json()["data"]["id"]

    # Create Found Report (Strong match - opposite type FOUND, same category, same cluster location)
    found_good = client.post(
        "/api/reports",
        json={
            "type": "FOUND",
            "item_name": "Blue Apple iPad Tablet with Stylus",
            "category": "ELECTRONICS",
            "description": "Found blue iPad tablet with white stylus pen on second floor study area.",
            "event_date": str(today),
            "location_text": "Library 2nd Floor Study Hall",
            "contact_name": "Finder",
            "contact_email": "finder@campus.edu",
        },
    )
    found_good_id = found_good.json()["data"]["id"]

    # Create Found Report (Unrelated - different category & location)
    found_unrelated = client.post(
        "/api/reports",
        json={
            "type": "FOUND",
            "item_name": "Silver Stainless Steel Thermos",
            "category": "OTHER",
            "description": "Metallic thermos bottle found in locker room.",
            "event_date": str(today - timedelta(days=5)),
            "location_text": "Sports Complex Locker Room",
            "contact_name": "Gym Staff",
            "contact_email": "gym@campus.edu",
        },
    )

    # Request matches for Lost Report
    matches_res = client.get(f"/api/reports/{lost_id}/matches")
    assert matches_res.status_code == 200
    res_body = matches_res.json()
    assert res_body["error"] is None

    matches = res_body["data"]["matches"]
    assert len(matches) >= 1

    top_match = matches[0]
    assert top_match["candidate"]["id"] == found_good_id
    assert top_match["total_score"] > 60.0
    assert top_match["components"]["category_score"] == 100.0
    assert top_match["components"]["date_score"] == 100.0
    assert "Potential match—not verified ownership" in top_match["disclaimer"]
    assert any("Same item category" in r for r in top_match["reasons"])

    # Resolve the found report and verify it is immediately removed from matches
    resolve_res = client.post(f"/api/reports/{found_good_id}/resolve")
    assert resolve_res.status_code == 200

    matches_after_resolve = client.get(f"/api/reports/{lost_id}/matches")
    assert matches_after_resolve.status_code == 200
    candidate_ids = [m["candidate"]["id"] for m in matches_after_resolve.json()["data"]["matches"]]
    assert found_good_id not in candidate_ids
