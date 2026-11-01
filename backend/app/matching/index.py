"""
In-Memory DSA Indexes for LostLink.
Implements:
1. Category Index: Category -> Set[ReportID]
2. Inverted Keyword Index: Token -> Set[ReportID]
3. Fast Report Store: ReportID -> ReportRecord
Provides deterministic candidate generation without full table scans.
"""
from dataclasses import dataclass
from datetime import date
from typing import Dict, Set, Optional, List
from collections import defaultdict
from app.matching.tokenizer import extract_tokens
from app.matching.heuristics import normalize_location


@dataclass(slots=True)
class ReportRecord:
    id: str
    type: str               # "LOST" or "FOUND"
    category: str           # "ELECTRONICS", etc.
    item_name: str
    description: str
    event_date: date
    location_text: str
    normalized_location: str
    status: str             # "ACTIVE", "RESOLVED", "HIDDEN"
    tokens: Set[str]
    community_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @classmethod
    def from_model(cls, model) -> "ReportRecord":
        combined_text = f"{model.item_name} {model.description}"
        tokens = extract_tokens(combined_text)
        return cls(
            id=str(model.id),
            type=str(model.type),
            category=str(model.category),
            item_name=str(model.item_name),
            description=str(model.description),
            event_date=model.event_date,
            location_text=str(model.location_text),
            normalized_location=normalize_location(model.location_text),
            status=str(model.status),
            tokens=tokens,
            community_id=str(model.community_id) if getattr(model, "community_id", None) else None,
            latitude=float(model.latitude) if getattr(model, "latitude", None) is not None else None,
            longitude=float(model.longitude) if getattr(model, "longitude", None) is not None else None,
        )


class MatchingIndex:
    """
    In-memory dual index:
    - category_index[category] = set(report_ids)
    - keyword_index[token] = set(report_ids)
    - type_index[type] = set(report_ids)
    - records[report_id] = ReportRecord
    """

    def __init__(self):
        self.category_index: Dict[str, Set[str]] = defaultdict(set)
        self.keyword_index: Dict[str, Set[str]] = defaultdict(set)
        self.type_index: Dict[str, Set[str]] = defaultdict(set)
        self.records: Dict[str, ReportRecord] = {}

    def clear(self) -> None:
        self.category_index.clear()
        self.keyword_index.clear()
        self.type_index.clear()
        self.records.clear()

    def add(self, record: ReportRecord) -> None:
        """Add active report to the in-memory indexes."""
        # Clean up any existing index postings for this ID first
        if record.id in self.records:
            self.remove(record.id)

        self.records[record.id] = record

        # Only ACTIVE records are eligible for matching indexes
        if record.status == "ACTIVE":
            self.type_index[record.type.upper()].add(record.id)
            self.category_index[record.category.upper()].add(record.id)
            for token in record.tokens:
                self.keyword_index[token].add(record.id)

    def remove(self, report_id: str) -> None:
        """Remove a report from all indexes."""
        record = self.records.pop(report_id, None)
        if record:
            type_key = record.type.upper()
            if type_key in self.type_index:
                self.type_index[type_key].discard(report_id)
                if not self.type_index[type_key]:
                    del self.type_index[type_key]

            cat_key = record.category.upper()
            if cat_key in self.category_index:
                self.category_index[cat_key].discard(report_id)
                if not self.category_index[cat_key]:
                    del self.category_index[cat_key]

            for token in record.tokens:
                if token in self.keyword_index:
                    self.keyword_index[token].discard(report_id)
                    if not self.keyword_index[token]:
                        del self.keyword_index[token]

    def update(self, record: ReportRecord) -> None:
        """Update existing record in indexes."""
        self.remove(record.id)
        self.add(record)

    def get(self, report_id: str) -> Optional[ReportRecord]:
        return self.records.get(report_id)

    def get_stats(self) -> Dict[str, any]:
        """Diagnostic metrics: total records, categories, tokens, and approximate memory footprint."""
        import sys
        record_count = len(self.records)
        token_count = len(self.keyword_index)
        category_count = len(self.category_index)
        active_lost = len(self.type_index.get("LOST", set()))
        active_found = len(self.type_index.get("FOUND", set()))
        approx_record_bytes = sum(sys.getsizeof(r) for r in self.records.values())
        return {
            "indexed_active_reports": record_count,
            "indexed_categories": category_count,
            "indexed_tokens": token_count,
            "active_lost": active_lost,
            "active_found": active_found,
            "approx_memory_bytes": approx_record_bytes,
        }

    def get_candidate_ids(self, source: ReportRecord) -> Set[str]:
        """
        Fast candidate ID generation:
        1. Candidates sharing exact compatible category or at least one descriptive token.
        2. Fast intersection against eligible active opposite-type records.
        3. Excludes source report ID and out-of-boundary records (date window, community).
        """
        opposite_type = "FOUND" if source.type.upper() == "LOST" else "LOST"
        eligible_type_ids = self.type_index.get(opposite_type)
        if not eligible_type_ids:
            return set()

        # 1. Category bucket
        cat_key = source.category.upper()
        candidate_ids: Set[str] = set()
        if cat_key in self.category_index:
            candidate_ids.update(self.category_index[cat_key])

        # 2. Inverted token index bucket
        for token in source.tokens:
            if token in self.keyword_index:
                candidate_ids.update(self.keyword_index[token])

        # 3. Intersect with active opposite-type records and discard source
        candidate_ids &= eligible_type_ids
        candidate_ids.discard(source.id)
        if not candidate_ids:
            return set()

        # 4. Filter candidate pool: within date window, same community
        max_days = settings.CANDIDATE_DATE_WINDOW_DAYS
        valid_candidates: Set[str] = set()
        for cid in candidate_ids:
            cand_rec = self.records.get(cid)
            if not cand_rec:
                continue
            # Community boundary check: if both have a community defined, they must match
            if source.community_id and cand_rec.community_id and source.community_id != cand_rec.community_id:
                continue
            days_gap = abs((source.event_date - cand_rec.event_date).days)
            if days_gap <= max_days:
                valid_candidates.add(cid)

        return valid_candidates

    def linear_scan_candidate_ids(self, source: ReportRecord) -> Set[str]:
        """
        Linear scan baseline: checks every stored record.
        Used for verification and benchmarking against the inverted index.
        """
        opposite_type = "FOUND" if source.type == "LOST" else "LOST"
        max_days = settings.CANDIDATE_DATE_WINDOW_DAYS
        return {
            cid for cid, rec in self.records.items()
            if cid != source.id and rec.status == "ACTIVE" and rec.type == opposite_type
            and (not source.community_id or not rec.community_id or source.community_id == rec.community_id)
            and abs((source.event_date - rec.event_date).days) <= max_days
        }


    def rebuild(self, models: List) -> None:
        """Rebuild entire index atomically from persisted database records."""
        self.clear()
        for model in models:
            record = ReportRecord.from_model(model)
            self.add(record)


from app.config import settings

# Global singleton matching index instance

matching_index = MatchingIndex()
