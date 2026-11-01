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


def test_community_endpoints_and_clusters(client):
    from app.main import app
    from app.services.auth_service import require_admin

    class _MockAdmin:
        id = "admin-test-0000-0000"
        role = "admin"
        is_active = True

    # 1. Create a community (authenticated via client's mock user)
    res = client.post(
        "/api/communities",
        json={
            "name": "North Tech Campus",
            "slug": "north-tech",
            "description": "Engineering and technology campus",
        },
    )
    assert res.status_code == 201
    comm = res.json()["data"]
    assert comm["slug"] == "north-tech"
    comm_id = comm["id"]

    # 2. Duplicate slug returns 409
    dup = client.post(
        "/api/communities",
        json={"name": "Duplicate", "slug": "north-tech"},
    )
    assert dup.status_code == 409

    # 3. List communities
    list_res = client.get("/api/communities")
    assert list_res.status_code == 200
    slugs = [c["slug"] for c in list_res.json()["data"]]
    assert "north-tech" in slugs

    # 4. Create facility cluster (requires admin)
    # First try as normal user -> 403 Forbidden
    non_admin_cluster = client.post(
        f"/api/communities/{comm_id}/clusters",
        json={"name": "Robotics Lab", "aliases": ["robotics lab", "mechatronics hall"]},
    )
    assert non_admin_cluster.status_code == 403

    # Now override with admin dependency
    app.dependency_overrides[require_admin] = lambda: _MockAdmin()
    try:
        admin_cluster = client.post(
            f"/api/communities/{comm_id}/clusters",
            json={"name": "Robotics Lab", "aliases": ["robotics lab", "mechatronics hall"]},
        )
        assert admin_cluster.status_code == 201
        assert admin_cluster.json()["data"]["name"] == "Robotics Lab"
    finally:
        app.dependency_overrides.pop(require_admin, None)

    # 5. List clusters
    clusters_res = client.get(f"/api/communities/{comm_id}/clusters")
    assert clusters_res.status_code == 200
    assert len(clusters_res.json()["data"]) >= 1
    assert clusters_res.json()["data"][0]["name"] == "Robotics Lab"


def test_matching_community_isolation_api(client):
    today = date.today()

    # Create Community A
    client.post("/api/communities", json={"name": "Campus Alpha", "slug": "campus-alpha"})
    # Create Community B
    client.post("/api/communities", json={"name": "Campus Beta", "slug": "campus-beta"})

    comm_a = client.get("/api/communities").json()["data"]
    id_a = next(c["id"] for c in comm_a if c["slug"] == "campus-alpha")
    id_b = next(c["id"] for c in comm_a if c["slug"] == "campus-beta")

    # Lost report in Alpha
    lost_a = client.post(
        "/api/reports",
        json={
            "type": "LOST",
            "item_name": "Silver Watch",
            "category": "JEWELRY_WATCHES",
            "description": "Silver wrist watch with metallic mesh band",
            "event_date": str(today),
            "location_text": "Cafeteria",
            "contact_name": "Alice",
            "contact_email": "alice@alpha.edu",
            "community_id": id_a,
        },
    ).json()["data"]["id"]

    # Found report in Alpha (should match)
    found_a = client.post(
        "/api/reports",
        json={
            "type": "FOUND",
            "item_name": "Silver Mesh Watch",
            "category": "JEWELRY_WATCHES",
            "description": "Found wrist watch with metallic band near food area",
            "event_date": str(today),
            "location_text": "Cafeteria",
            "contact_name": "Bob",
            "contact_email": "bob@alpha.edu",
            "community_id": id_a,
        },
    ).json()["data"]["id"]

    # Found report in Beta (should NOT match)
    found_b = client.post(
        "/api/reports",
        json={
            "type": "FOUND",
            "item_name": "Silver Mesh Watch",
            "category": "JEWELRY_WATCHES",
            "description": "Found wrist watch with metallic band near food area",
            "event_date": str(today),
            "location_text": "Cafeteria",
            "contact_name": "Charlie",
            "contact_email": "charlie@beta.edu",
            "community_id": id_b,
        },
    ).json()["data"]["id"]

    # Match request for lost_a
    matches = client.get(f"/api/reports/{lost_a}/matches").json()["data"]["matches"]
    candidate_ids = [m["candidate"]["id"] for m in matches]

    assert found_a in candidate_ids
    assert found_b not in candidate_ids


def test_matching_gps_coordinates_api(client):
    today = date.today()

    # Lost report with coordinates
    lost = client.post(
        "/api/reports",
        json={
            "type": "LOST",
            "item_name": "Red Backpack",
            "category": "BAGS_WALLETS",
            "description": "Red JanSport backpack containing textbook",
            "event_date": str(today),
            "location_text": "Engineering Lawn",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "contact_name": "Dan",
            "contact_email": "dan@nyu.edu",
        },
    ).json()["data"]["id"]

    # Found report nearby (~50 meters offset)
    found_near = client.post(
        "/api/reports",
        json={
            "type": "FOUND",
            "item_name": "Red JanSport Bag",
            "category": "BAGS_WALLETS",
            "description": "Found red backpack on grass lawn",
            "event_date": str(today),
            "location_text": "Lawn Area",
            "latitude": 40.7132,
            "longitude": -74.0060,
            "contact_name": "Security",
            "contact_email": "sec@nyu.edu",
        },
    ).json()["data"]["id"]

    matches = client.get(f"/api/reports/{lost}/matches").json()["data"]["matches"]
    assert len(matches) >= 1
    top_match = matches[0]
    assert top_match["candidate"]["id"] == found_near
    assert top_match["components"]["location_score"] == 100.0

