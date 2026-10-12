"""
LostLink Matching Engine: deterministic scoring, heap ranking, and reason generation.
Implements:
- Weighted heuristic formula: S = 0.35C + 0.25L + 0.20D + 0.20K
- Priority queue (bounded min-heap) for top-N ranking
- Linear scan fallback for verification
- Transparent human-readable explanations
"""
import heapq
from dataclasses import dataclass, field
from typing import List, Tuple, Set
from app.config import settings
from app.matching.index import ReportRecord, matching_index
from app.matching.heuristics import (
    calculate_category_score,
    calculate_location_score,
    calculate_date_score,
)
from app.matching.tokenizer import calculate_jaccard_similarity


@dataclass(order=True)
class ScoredMatch:
    # Priority queue sort key: (-total_score, days_diff, candidate_id)
    # Note: We use negative score in standard min-heap to keep highest scores
    sort_key: Tuple[float, int, str] = field(init=False)
    total_score: float = field(compare=False)
    category_score: float = field(compare=False)
    location_score: float = field(compare=False)
    date_score: float = field(compare=False)
    keyword_score: float = field(compare=False)
    days_diff: int = field(compare=False)
    shared_keywords: List[str] = field(compare=False)
    reasons: List[str] = field(compare=False)
    candidate_id: str = field(compare=False)
    disclaimer: str = field(default="Potential match—not verified ownership", compare=False)

    def __post_init__(self):
        # In a min-heap retaining top N, we compare (total_score, -days_diff, inverted id)
        # For straightforward descending sort:
        self.sort_key = (-round(self.total_score, 2), self.days_diff, self.candidate_id)


def score_candidate(source: ReportRecord, candidate: ReportRecord) -> ScoredMatch:
    """Calculates all component scores and plain-language reasons."""
    # 1. Category
    c_score, c_reason = calculate_category_score(source.category, candidate.category)

    # 2. Location
    l_score, l_reason = calculate_location_score(source.location_text, candidate.location_text)

    # 3. Date
    d_score, d_reason, days_diff = calculate_date_score(source.event_date, candidate.event_date)

    # 4. Keyword / Jaccard
    k_score = calculate_jaccard_similarity(source.tokens, candidate.tokens)
    shared_tokens = sorted(list(source.tokens.intersection(candidate.tokens)))

    # Compute weighted total score
    w_c = settings.WEIGHT_CATEGORY
    w_l = settings.WEIGHT_LOCATION
    w_d = settings.WEIGHT_DATE
    w_k = settings.WEIGHT_KEYWORD

    total = (w_c * c_score) + (w_l * l_score) + (w_d * d_score) + (w_k * k_score)
    total_score = round(max(0.0, min(100.0, total)), 2)

    # Generate plain-English reasons
    reasons = [c_reason, l_reason, d_reason]
    if shared_tokens:
        reasons.append(f"Shared keywords: {', '.join(shared_tokens[:6])}")
    elif k_score == 0.0 and (not source.tokens or not candidate.tokens):
        reasons.append("No descriptive keywords shared")

    return ScoredMatch(
        total_score=total_score,
        category_score=round(c_score, 2),
        location_score=round(l_score, 2),
        date_score=round(d_score, 2),
        keyword_score=round(k_score, 2),
        days_diff=days_diff,
        shared_keywords=shared_tokens,
        reasons=reasons,
        candidate_id=candidate.id,
    )


class MatchingEngine:
    @staticmethod
    def sort_candidates_full(scored_matches: List[ScoredMatch]) -> List[ScoredMatch]:
        """
        Complete deterministic sort in O(C log C).
        Order: total_score DESC, days_diff ASC, candidate_id ASC.
        """
        return sorted(
            scored_matches,
            key=lambda m: (-m.total_score, m.days_diff, m.candidate_id),
        )

    @staticmethod
    def rank_candidates_heap(
        scored_matches: List[ScoredMatch],
        top_n: int = 5
    ) -> List[ScoredMatch]:
        """
        Uses a bounded min-heap to extract the top-N results deterministically in O(C log N).
        Tie-breaking rule:
        1. total_score DESC
        2. days_diff ASC
        3. candidate_id ASC
        """
        if not scored_matches:
            return []


        # Python heapq is a min-heap.
        # To maintain the top N maximum elements:
        # We store elements with an inverted sort tuple: (total_score, -days_diff, candidate_id_desc)
        # So the smallest of the top N sits at heap root and gets popped.
        # Alternatively, we can sort directly if C is small, or use nlargest.
        # To demonstrate DSA priority-queue rigor explicitly:
        class HeapItem:
            def __init__(self, match: ScoredMatch):
                self.match = match
                # Min-heap key: lowest score is smallest; if scores tie, higher days_diff is smallest;
                # if days_diff tie, lex-larger id is smallest (so it gets evicted).
                self.key = (match.total_score, -match.days_diff, match.candidate_id)

            def __lt__(self, other):
                # When comparing in min-heap:
                if self.match.total_score != other.match.total_score:
                    return self.match.total_score < other.match.total_score
                if self.match.days_diff != other.match.days_diff:
                    return self.match.days_diff > other.match.days_diff
                return self.match.candidate_id > other.match.candidate_id

        heap: List[HeapItem] = []
        for item in scored_matches:
            heap_item = HeapItem(item)
            if len(heap) < top_n:
                heapq.heappush(heap, heap_item)
            else:
                if heap_item > heap[0]:
                    heapq.heappushpop(heap, heap_item)

        # Extract items and sort in proper descending order
        top_items = [h.match for h in heap]
        top_items.sort(key=lambda m: (-m.total_score, m.days_diff, m.candidate_id))
        return top_items

    @classmethod
    def match_report(
        cls,
        source: ReportRecord,
        limit: int = 5,
        min_score: float = 0.0,
        use_linear_fallback: bool = False,
    ) -> Tuple[List[ScoredMatch], int]:
        """
        Executes candidate generation, scoring, and ranking.
        Returns: (ranked_matches, total_candidate_pool_size)
        """
        if source.status != "ACTIVE":
            return [], 0

        # 1. Candidate ID generation (Index vs Linear Fallback)
        if use_linear_fallback:
            candidate_ids = matching_index.linear_scan_candidate_ids(source)
        else:
            candidate_ids = matching_index.get_candidate_ids(source)

        total_pool_size = len(candidate_ids)
        if not candidate_ids:
            return [], 0

        # 2. Score candidate reports
        scored: List[ScoredMatch] = []
        for cid in candidate_ids:
            cand_rec = matching_index.get(cid)
            if not cand_rec:
                continue

            match = score_candidate(source, cand_rec)
            if match.total_score >= min_score:
                scored.append(match)

        # 3. Deterministic Top-N Heap Selection
        ranked = cls.rank_candidates_heap(scored, top_n=limit)
        return ranked, total_pool_size
