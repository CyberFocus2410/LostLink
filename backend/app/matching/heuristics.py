"""
Heuristic rules and scoring components for LostLink matching engine.
Heuristic weights, location alias dictionary, category compatibility, and date decay.
"""
from datetime import date
from typing import Tuple, Dict, Set
from app.config import settings

# Campus location clusters / aliases for proximity scoring (Score = 70.0)
LOCATION_CLUSTERS: Dict[str, Set[str]] = {
    "library": {
        "library", "main library", "library 1st floor", "library 2nd floor",
        "library 3rd floor", "library cafe", "study hall", "quiet study",
        "library circulation desk", "stacks"
    },
    "student_center": {
        "student center", "student union", "food court", "cafeteria",
        "dining hall", "campus bookstore", "lounge", "atrium"
    },
    "gym_sports": {
        "gym", "recreation center", "sports complex", "basketball court",
        "weight room", "locker room", "swimming pool", "fitness center"
    },
    "science_complex": {
        "science hall", "physics lab", "chemistry building", "engineering hall",
        "computer lab", "tech wing", "hall a", "hall b"
    },
    "admin_quad": {
        "admin building", "admissions", "quad", "campus green",
        "bursar office", "registrar", "main lawn"
    }
}


def normalize_location(location: str) -> str:
    """Normalize location string for consistent comparison."""
    if not location:
        return ""
    import re
    cleaned = re.sub(r"[^\w\s]", " ", location.lower())
    return " ".join(cleaned.split()).strip()


def calculate_category_score(cat_a: str, cat_b: str) -> Tuple[float, str]:
    """
    Computes category compatibility score (0-100).
    Exact match: 100.0
    Incompatible: 0.0
    """
    if not cat_a or not cat_b:
        return 0.0, "Category missing"

    norm_a = cat_a.strip().upper()
    norm_b = cat_b.strip().upper()

    if norm_a == norm_b:
        return 100.0, f"Same item category ({norm_a})"

    return 0.0, f"Incompatible categories ({norm_a} vs {norm_b})"


def calculate_location_score(loc_a: str, loc_b: str) -> Tuple[float, str]:
    """
    Computes location proximity score (0-100).
    Exact match: 100.0
    Nearby / same cluster: 70.0
    Unrelated: 0.0
    """
    norm_a = normalize_location(loc_a)
    norm_b = normalize_location(loc_b)

    if not norm_a or not norm_b:
        return 0.0, "Location unspecified"

    if norm_a == norm_b:
        return 100.0, f"Identical reported location ({loc_a.strip()})"

    # Check if both belong to the same cluster/alias
    for cluster_name, aliases in LOCATION_CLUSTERS.items():
        if (norm_a in aliases or any(a in norm_a for a in aliases)) and \
           (norm_b in aliases or any(b in norm_b for b in aliases)):
            clean_cluster = cluster_name.replace("_", " ").title()
            return 70.0, f"Nearby area in same facility ({clean_cluster})"

    return 0.0, f"Different locations ({loc_a.strip()} vs {loc_b.strip()})"


def calculate_date_score(date_a: date, date_b: date) -> Tuple[float, str, int]:
    """
    Computes date proximity score:
    D = max(0.0, 100.0 - DATE_DECAY_RATE * absolute_days_gap)
    """
    days_diff = abs((date_a - date_b).days)
    decay = settings.DATE_DECAY_RATE
    raw_score = 100.0 - (decay * days_diff)
    score = max(0.0, raw_score)

    if days_diff == 0:
        reason = "Same reported date"
    elif days_diff == 1:
        reason = "1 day apart"
    else:
        reason = f"{days_diff} days apart"

    return round(score, 2), reason, days_diff
