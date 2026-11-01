"""
Comprehensive DSA Unit Tests for LostLink Matching Engine.
Covers:
- Exact & partial matching
- Unrelated category rejection
- Same-type exclusion (LOST vs LOST, FOUND vs FOUND)
- Resolved / hidden exclusion
- Empty descriptions and token sets
- Punctuation & case normalization
- Date decay boundaries
- Deterministic tie-breaking (Score DESC -> Date ASC -> ID ASC)
- Index consistency on add / update / resolve / remove
- Correctness equivalence of Linear Scan vs Inverted Index
"""
import pytest
from datetime import date, timedelta

from app.matching.tokenizer import normalize_text, extract_tokens, calculate_jaccard_similarity
from app.matching.heuristics import (
    calculate_category_score,
    calculate_location_score,
    calculate_date_score,
    normalize_location,
    haversine_distance_meters,
    calculate_haversine_location_score,
)
from app.matching.index import MatchingIndex, ReportRecord
from app.matching.engine import MatchingEngine, score_candidate


def make_record(
    report_id: str,
    report_type: str,
    category: str,
    item_name: str,
    description: str,
    days_ago: int = 0,
    location_text: str = "Library 2nd Floor",
    status: str = "ACTIVE",
) -> ReportRecord:
    combined = f"{item_name} {description}"
    return ReportRecord(
        id=report_id,
        type=report_type,
        category=category,
        item_name=item_name,
        description=description,
        event_date=date.today() - timedelta(days=days_ago),
        location_text=location_text,
        normalized_location=normalize_location(location_text),
        status=status,
        tokens=extract_tokens(combined),
    )


# --- 1. Text Normalization and Tokenization ---

def test_text_normalization():
    raw = "  Apple MacBook Pro (16-inch, M3)!!! Left @ Library #StudyRoom...  "
    norm = normalize_text(raw)
    assert "!" not in norm
    assert "@" not in norm
    assert "#" not in norm
    assert norm == "apple macbook pro 16-inch m3 left library studyroom"


def test_token_extraction_and_stop_words():
    text = "Found a lost black leather wallet near the cafeteria for someone."
    tokens = extract_tokens(text)
    # Stop words like 'a', 'the', 'near', 'for', 'someone' must be filtered
    assert "the" not in tokens
    assert "for" not in tokens
    assert "someone" not in tokens
    # Key tokens must be preserved
    assert "black" in tokens
    assert "leather" in tokens
    assert "wallet" in tokens
    assert "cafeteria" in tokens


# --- 2. Jaccard Keyword Similarity Rules ---

def test_jaccard_similarity_empty_and_exact():
    assert calculate_jaccard_similarity(set(), {"wallet", "black"}) == 0.0
    assert calculate_jaccard_similarity({"wallet"}, set()) == 0.0
    assert calculate_jaccard_similarity(set(), set()) == 0.0

    # Exact match: 100.0
    set_a = {"macbook", "silver", "laptop"}
    assert calculate_jaccard_similarity(set_a, set_a) == 100.0

    # Partial overlap: Intersection = 2, Union = 4 -> 2/4 * 100 = 50.0
    set_b = {"macbook", "silver", "pro", "charger"}
    score = calculate_jaccard_similarity({"macbook", "silver"}, set_b)
    assert score == 50.0


# --- 3. Category & Location Compatibility ---

def test_category_compatibility_rules():
    score, reason = calculate_category_score("ELECTRONICS", "ELECTRONICS")
    assert score == 100.0
    assert "Same item category" in reason

    score_incomp, reason_incomp = calculate_category_score("ELECTRONICS", "CLOTHING")
    assert score_incomp == 0.0
    assert "Incompatible" in reason_incomp


def test_location_proximity_rules():
    # Exact location
    s_exact, _ = calculate_location_score("Library 2nd Floor", "library 2nd floor")
    assert s_exact == 100.0

    # Configured alias / cluster ("Main Library" and "Library Cafe")
    s_alias, r_alias = calculate_location_score("Main Library", "Library Cafe")
    assert s_alias == 70.0
    assert "Nearby area" in r_alias

    # Unrelated location
    s_none, _ = calculate_location_score("Library 2nd Floor", "Gym Basketball Court")
    assert s_none == 0.0


# --- 4. Date Proximity and Decay Boundaries ---

def test_date_decay_boundaries():
    today = date.today()

    # Same day: 0 days diff -> 100.0
    s0, _, diff0 = calculate_date_score(today, today)
    assert s0 == 100.0
    assert diff0 == 0

    # 1 day apart -> 100 - 15*1 = 85.0
    s1, _, diff1 = calculate_date_score(today, today - timedelta(days=1))
    assert s1 == 85.0
    assert diff1 == 1

    # 3 days apart -> 100 - 15*3 = 55.0
    s3, _, diff3 = calculate_date_score(today, today - timedelta(days=3))
    assert s3 == 55.0
    assert diff3 == 3

    # 6 days apart -> 100 - 15*6 = 10.0
    s6, _, diff6 = calculate_date_score(today, today - timedelta(days=6))
    assert s6 == 10.0

    # 7 days apart -> max(0, 100 - 15*7 = -5) -> 0.0
    s7, _, diff7 = calculate_date_score(today, today - timedelta(days=7))
    assert s7 == 0.0

    # 30 days apart -> 0.0
    s30, _, _ = calculate_date_score(today, today - timedelta(days=30))
    assert s30 == 0.0


# --- 5. Candidate Generation & Index Exclusions ---

def test_opposite_type_exclusion_and_same_type_filtering():
    idx = MatchingIndex()
    lost_source = make_record("L1", "LOST", "ELECTRONICS", "iPhone 15", "Black phone")
    same_type = make_record("L2", "LOST", "ELECTRONICS", "iPhone 15", "Black phone")
    opposite_cand = make_record("F1", "FOUND", "ELECTRONICS", "iPhone 15", "Black phone")

    idx.add(lost_source)
    idx.add(same_type)
    idx.add(opposite_cand)

    candidates = idx.get_candidate_ids(lost_source)
    assert "F1" in candidates
    assert "L2" not in candidates  # Same type must be excluded
    assert "L1" not in candidates  # Source report must not match itself


def test_resolved_and_hidden_reports_excluded():
    idx = MatchingIndex()
    lost_source = make_record("L1", "LOST", "BAGS_WALLETS", "Leather Wallet", "Brown bellroy")
    found_resolved = make_record("F1", "FOUND", "BAGS_WALLETS", "Leather Wallet", "Brown bellroy", status="RESOLVED")
    found_hidden = make_record("F2", "FOUND", "BAGS_WALLETS", "Leather Wallet", "Brown bellroy", status="HIDDEN")
    found_active = make_record("F3", "FOUND", "BAGS_WALLETS", "Leather Wallet", "Brown bellroy", status="ACTIVE")

    idx.add(lost_source)
    idx.add(found_resolved)
    idx.add(found_hidden)
    idx.add(found_active)

    candidates = idx.get_candidate_ids(lost_source)
    assert "F3" in candidates
    assert "F1" not in candidates  # RESOLVED excluded
    assert "F2" not in candidates  # HIDDEN excluded


def test_no_candidates_available():
    idx = MatchingIndex()
    lost_source = make_record("L1", "LOST", "ELECTRONICS", "MacBook Pro", "Apple laptop")
    idx.add(lost_source)

    # Empty candidate pool returns empty matches list without error
    candidates = idx.get_candidate_ids(lost_source)
    assert len(candidates) == 0

    matches, pool_size = MatchingEngine.match_report(lost_source)
    assert matches == []
    assert pool_size == 0


def test_empty_description_handling():
    source = make_record("L1", "LOST", "CLOTHING", "Jacket", "   ")
    cand = make_record("F1", "FOUND", "CLOTHING", "Coat", "...")
    match = score_candidate(source, cand)

    # Keyword score should safely be 0.0
    assert match.keyword_score == 0.0
    assert match.category_score == 100.0


# --- 6. Deterministic Tie-Breaking (Score DESC -> Days ASC -> ID ASC) ---

def test_deterministic_tie_breaking():
    source = make_record("L1", "LOST", "KEYS_CARDS", "Key Fob", "Car keys", days_ago=0)

    # Create 3 candidates with identical scores:
    # Cand A: 2 days gap, ID="cand_b"
    # Cand B: 2 days gap, ID="cand_a" (lexicographically smaller)
    # Cand C: 1 day gap, ID="cand_c" (smaller date gap -> ranks higher)
    c1 = make_record("cand_b", "FOUND", "KEYS_CARDS", "Key Fob", "Car keys", days_ago=2, location_text=source.location_text)
    c2 = make_record("cand_a", "FOUND", "KEYS_CARDS", "Key Fob", "Car keys", days_ago=2, location_text=source.location_text)
    c3 = make_record("cand_c", "FOUND", "KEYS_CARDS", "Key Fob", "Car keys", days_ago=1, location_text=source.location_text)

    s1 = score_candidate(source, c1)
    s2 = score_candidate(source, c2)
    s3 = score_candidate(source, c3)

    # c3 has smaller date gap -> higher date score -> higher total score
    assert s3.total_score > s1.total_score

    # s1 and s2 have identical scores and identical date gaps:
    assert s1.total_score == s2.total_score
    assert s1.days_diff == s2.days_diff

    # Test Bounded Min-Heap ranking
    heap_ranked = MatchingEngine.rank_candidates_heap([s1, s2, s3], top_n=3)
    # Test Full Sort ranking
    full_ranked = MatchingEngine.sort_candidates_full([s1, s2, s3])

    # Both algorithms must agree deterministically:
    assert [m.candidate_id for m in heap_ranked] == ["cand_c", "cand_a", "cand_b"]
    assert [m.candidate_id for m in full_ranked] == ["cand_c", "cand_a", "cand_b"]


# --- 7. Index Consistency on Create, Edit, and Resolve ---

def test_index_consistency_lifecycle():
    idx = MatchingIndex()
    rec = make_record("R1", "LOST", "ELECTRONICS", "iPad Pro", "Silver tablet with pencil")
    idx.add(rec)

    assert "ELECTRONICS" in idx.category_index
    assert "R1" in idx.category_index["ELECTRONICS"]
    assert "tablet" in idx.keyword_index
    assert "R1" in idx.keyword_index["tablet"]

    # Update description to remove "pencil" and add "keyboard"
    updated_rec = make_record("R1", "LOST", "ELECTRONICS", "iPad Pro", "Silver tablet with magic keyboard")
    idx.update(updated_rec)

    assert "keyboard" in idx.keyword_index
    assert "R1" in idx.keyword_index["keyboard"]
    assert "pencil" not in idx.keyword_index  # Old token cleanly pruned

    # Mark as RESOLVED
    resolved_rec = make_record("R1", "LOST", "ELECTRONICS", "iPad Pro", "Silver tablet with magic keyboard", status="RESOLVED")
    idx.update(resolved_rec)

    # Resolved report must no longer appear in candidate index postings
    assert "R1" not in idx.category_index.get("ELECTRONICS", set())
    assert "R1" not in idx.keyword_index.get("keyboard", set())


# --- 8. Linear Scan vs Inverted Index Correctness ---

def test_inverted_index_vs_linear_scan_equivalence():
    idx = MatchingIndex()
    source = make_record("L1", "LOST", "ELECTRONICS", "ThinkPad Laptop", "Black laptop")
    idx.add(source)

    for i in range(20):
        # Even: opposite type FOUND
        t = "FOUND" if i % 2 == 0 else "LOST"
        cat = "ELECTRONICS" if i % 3 == 0 else "OTHER"
        cand = make_record(f"C_{i}", t, cat, f"Item {i}", f"Description {i} laptop", days_ago=i % 10)
        idx.add(cand)

    inverted_candidates = idx.get_candidate_ids(source)
    linear_candidates = idx.linear_scan_candidate_ids(source)

    # Inverted index candidates must all be valid opposite-type candidates present in linear scan
    for cid in inverted_candidates:
        assert cid in linear_candidates


# --- 9. Phase 2: Haversine Coordinates & Multi-Community Tests ---

def test_haversine_distance_calculation():
    # Known distance: Eiffel Tower (48.8584, 2.2945) to Louvre Museum (48.8606, 2.3376) ~ 3.16 km
    dist = haversine_distance_meters(48.8584, 2.2945, 48.8606, 2.3376)
    assert 3100 <= dist <= 3300

    # Same point distance is 0
    assert haversine_distance_meters(40.7128, -74.0060, 40.7128, -74.0060) == 0.0


def test_haversine_location_scoring_bands():
    lat, lon = 37.7749, -122.4194

    # Band 1: <= 100 meters -> 100.0 (e.g. ~50m offset)
    # 0.00045 degrees lat is ~50 meters
    score, exp = calculate_haversine_location_score(lat, lon, lat + 0.00045, lon)
    assert score == 100.0
    assert "within 100m" in exp

    # Band 2: <= 1000 meters -> 70.0 (e.g. ~500m offset)
    # 0.0045 degrees lat is ~500 meters
    score, exp = calculate_haversine_location_score(lat, lon, lat + 0.0045, lon)
    assert score == 70.0
    assert "within 1km" in exp

    # Band 3: > 1000 meters -> 0.0 (e.g. ~2km offset)
    # 0.02 degrees lat is ~2200 meters
    score, exp = calculate_haversine_location_score(lat, lon, lat + 0.02, lon)
    assert score == 0.0
    assert "too large" in exp


def test_matching_engine_haversine_integration():
    source = make_record("SRC_1", "LOST", "ELECTRONICS", "Earbuds", "Sony wireless earbuds")
    source.latitude = 37.7749
    source.longitude = -122.4194

    # Candidate 1: nearby (<100m)
    cand_near = make_record("CAND_NEAR", "FOUND", "ELECTRONICS", "Earbuds", "Found earbuds")
    cand_near.latitude = 37.7749 + 0.0004
    cand_near.longitude = -122.4194

    # Candidate 2: far (>1000m)
    cand_far = make_record("CAND_FAR", "FOUND", "ELECTRONICS", "Earbuds", "Found earbuds")
    cand_far.latitude = 37.7749 + 0.02
    cand_far.longitude = -122.4194

    # Candidate 3: missing coordinates (falls back to text cluster)
    cand_fallback = make_record("CAND_FALLBACK", "FOUND", "ELECTRONICS", "Earbuds", "Found earbuds", location_text="Library 2nd Floor")

    comp_near = score_candidate(source, cand_near)
    assert comp_near.location_score == 100.0
    assert any("proximity" in r.lower() for r in comp_near.reasons)

    comp_far = score_candidate(source, cand_far)
    assert comp_far.location_score == 0.0

    comp_fallback = score_candidate(source, cand_fallback)
    # source has location_text="Library 2nd Floor" by make_record default, so text match applies
    assert comp_fallback.location_score == 100.0


def test_community_isolation_in_indexing():
    idx = MatchingIndex()

    # Source in Community Alpha
    source = make_record("SRC_COMM", "LOST", "ELECTRONICS", "Tablet", "Samsung Galaxy tablet")
    source.community_id = "comm_alpha"
    idx.add(source)

    # Candidate 1: same community Alpha
    cand1 = make_record("CAND_ALPHA", "FOUND", "ELECTRONICS", "Tablet", "Samsung tablet")
    cand1.community_id = "comm_alpha"
    idx.add(cand1)

    # Candidate 2: different community Beta
    cand2 = make_record("CAND_BETA", "FOUND", "ELECTRONICS", "Tablet", "Samsung tablet")
    cand2.community_id = "comm_beta"
    idx.add(cand2)

    # Candidate 3: unassigned community (legacy / global)
    cand3 = make_record("CAND_GLOBAL", "FOUND", "ELECTRONICS", "Tablet", "Samsung tablet")
    cand3.community_id = None
    idx.add(cand3)

    candidates = idx.get_candidate_ids(source)
    assert "CAND_ALPHA" in candidates
    assert "CAND_BETA" not in candidates  # Isolated!
    assert "CAND_GLOBAL" in candidates  # Global matches both

    # Also verify linear scan produces identical isolation
    linear_cands = idx.linear_scan_candidate_ids(source)
    assert "CAND_ALPHA" in linear_cands
    assert "CAND_BETA" not in linear_cands
    assert "CAND_GLOBAL" in linear_cands

