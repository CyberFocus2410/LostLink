"""
LostLink DSA Matching Engine Benchmark Script.
Compares Linear Scan vs Inverted Index candidate retrieval and
Bounded Min-Heap vs Full Sort ranking across reproducible seeded datasets.
"""
import time
import random
import sys
from pathlib import Path
from datetime import date, timedelta
from typing import List

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.matching.index import MatchingIndex, ReportRecord
from app.matching.tokenizer import extract_tokens

from app.matching.heuristics import normalize_location
from app.matching.engine import MatchingEngine, score_candidate

# Reproducibility seed
SEED = 42

CATEGORIES = [
    "ELECTRONICS", "KEYS_CARDS", "BAGS_WALLETS", "CLOTHING",
    "DOCUMENTS_BOOKS", "JEWELRY_WATCHES", "OTHER"
]

LOCATIONS = [
    "Main Library 2nd Floor", "Library Cafe", "Student Union Food Court",
    "Campus Bookstore", "Recreation Center Locker Room", "Sports Complex Gym",
    "Science Hall Lab 102", "Physics Hall Wing B", "Admin Quad Main Lawn"
]

SAMPLE_WORDS = [
    "apple", "macbook", "pro", "silver", "laptop", "charger", "cord", "iphone",
    "case", "black", "leather", "wallet", "id", "card", "keys", "honda", "lanyard",
    "red", "blue", "backpack", "notebook", "calculator", "watch", "casio", "ring",
    "gold", "umbrella", "flask", "bottle", "jacket", "hoodie", "pencil", "glasses"
]


def generate_synthetic_dataset(size: int) -> List[ReportRecord]:
    random.seed(SEED)
    today = date.today()
    records = []

    for i in range(size):
        t = "FOUND" if random.random() < 0.6 else "LOST"
        cat = random.choice(CATEGORIES)
        loc = random.choice(LOCATIONS)
        days_ago = random.randint(0, 25)
        event_date = today - timedelta(days=days_ago)

        word_count = random.randint(4, 10)
        chosen_words = random.sample(SAMPLE_WORDS, min(word_count, len(SAMPLE_WORDS)))
        item_name = f"{chosen_words[0].capitalize()} {chosen_words[1]}"
        description = " ".join(chosen_words)

        combined = f"{item_name} {description}"
        tokens = extract_tokens(combined)

        rec = ReportRecord(
            id=f"SYNTH_{i:05d}",
            type=t,
            category=cat,
            item_name=item_name,
            description=description,
            event_date=event_date,
            location_text=loc,
            normalized_location=normalize_location(loc),
            status="ACTIVE",
            tokens=tokens,
        )
        records.append(rec)

    return records


def run_benchmark(dataset_sizes=(500, 2000, 5000), num_queries=50):
    print("=" * 80)
    print("LOSTLINK DSA PERFORMANCE BENCHMARK (MEASURED TIMINGS)")
    print(f"Random Seed: {SEED} | Query Repetitions: {num_queries} per dataset")
    print("=" * 80)
    print(f"{'Dataset Size':<14} | {'Method':<20} | {'Avg Cand Gen (ms)':<18} | {'Avg Total Match (ms)':<20} | {'Speedup':<8}")
    print("-" * 80)

    for size in dataset_sizes:
        records = generate_synthetic_dataset(size)
        idx = MatchingIndex()
        for r in records:
            idx.add(r)

        # Pick queries (LOST reports)
        queries = [r for r in records if r.type == "LOST"][:num_queries]
        if not queries:
            queries = records[:num_queries]

        # 1. Benchmark Inverted Index Candidate Generation & Matching
        t0 = time.perf_counter()
        inv_candidate_counts = []
        for q in queries:
            cids = idx.get_candidate_ids(q)
            inv_candidate_counts.append(len(cids))
            # Score and heap rank
            scored = [score_candidate(q, idx.get(cid)) for cid in cids if idx.get(cid)]
            MatchingEngine.rank_candidates_heap(scored, top_n=5)
        t_index_total = (time.perf_counter() - t0) * 1000.0 / len(queries)

        t0_gen = time.perf_counter()
        for q in queries:
            idx.get_candidate_ids(q)
        t_index_gen = (time.perf_counter() - t0_gen) * 1000.0 / len(queries)

        # 2. Benchmark Linear Scan Candidate Generation & Matching
        t0_lin = time.perf_counter()
        for q in queries:
            cids = idx.linear_scan_candidate_ids(q)
            scored = [score_candidate(q, idx.get(cid)) for cid in cids if idx.get(cid)]
            MatchingEngine.rank_candidates_heap(scored, top_n=5)
        t_linear_total = (time.perf_counter() - t0_lin) * 1000.0 / len(queries)

        t0_lin_gen = time.perf_counter()
        for q in queries:
            idx.linear_scan_candidate_ids(q)
        t_linear_gen = (time.perf_counter() - t0_lin_gen) * 1000.0 / len(queries)

        speedup = t_linear_total / max(t_index_total, 0.0001)

        print(f"{size:<14} | {'Linear Scan':<20} | {t_linear_gen:<18.4f} | {t_linear_total:<20.4f} | {'1.00x':<8}")
        print(f"{size:<14} | {'Inverted Index (DSA)':<20} | {t_index_gen:<18.4f} | {t_index_total:<20.4f} | {f'{speedup:.2f}x':<8}")
        print("-" * 80)

    # 3. Ranking Benchmark: Bounded Min-Heap vs Full Sort
    print("\n" + "=" * 80)
    print("RANKING ALGORITHM COMPARISON: Bounded Min-Heap O(c log K) vs Full Sort O(c log c)")
    print("=" * 80)

    test_candidate_counts = [50, 200, 1000, 5000]
    top_k = 5

    for c_count in test_candidate_counts:
        # Generate dummy scored matches
        matches = []
        for i in range(c_count):
            from app.matching.engine import ScoredMatch
            matches.append(
                ScoredMatch(
                    total_score=random.uniform(10.0, 95.0),
                    category_score=100.0,
                    location_score=70.0,
                    date_score=55.0,
                    keyword_score=30.0,
                    days_diff=random.randint(0, 10),
                    shared_keywords=["item"],
                    reasons=["match"],
                    candidate_id=f"cand_{i}",
                )
            )

        # Time Heap
        t0 = time.perf_counter()
        for _ in range(100):
            MatchingEngine.rank_candidates_heap(matches, top_n=top_k)
        t_heap = (time.perf_counter() - t0) * 1000.0 / 100.0

        # Time Full Sort
        t0 = time.perf_counter()
        for _ in range(100):
            sorted_items = MatchingEngine.sort_candidates_full(matches)[:top_k]
        t_sort = (time.perf_counter() - t0) * 1000.0 / 100.0

        print(f"Candidates: {c_count:<5} | Top-K: {top_k} | Min-Heap: {t_heap:.4f} ms | Full Sort: {t_sort:.4f} ms")


if __name__ == "__main__":
    run_benchmark()
