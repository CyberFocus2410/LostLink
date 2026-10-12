"""
Tokenizer and text normalization for LostLink matching engine.
Transforms unstructured text into clean normalized keyword tokens.
"""
import re
from typing import Set

# Standard campus / lost & found stop words to exclude generic noise
STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "up", "about", "into", "over", "after", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "but", "if", "or", "because", "as", "until", "while", "this", "that", "these",
    "those", "my", "your", "his", "her", "its", "our", "their", "item", "lost",
    "found", "please", "help", "reward", "near", "around", "left", "someone", "anyone"
}

# Regex to remove punctuation and non-alphanumeric chars (preserving words and digits)
PUNCTUATION_REGEX = re.compile(r"[^\w\s-]", re.UNICODE)
WHITESPACE_REGEX = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, and collapse whitespace."""
    if not text:
        return ""
    lowered = text.lower()
    cleaned = PUNCTUATION_REGEX.sub(" ", lowered)
    collapsed = WHITESPACE_REGEX.sub(" ", cleaned).strip()
    return collapsed


def extract_tokens(text: str) -> Set[str]:
    """
    Extracts unique significant tokens from text, removing stop words
    and tokens with length < 2.
    """
    normalized = normalize_text(text)
    if not normalized:
        return set()

    tokens = set()
    for word in normalized.split(" "):
        clean_word = word.strip("-_")
        if len(clean_word) >= 2 and clean_word not in STOP_WORDS and not clean_word.isdigit():
            tokens.add(clean_word)
        elif len(clean_word) >= 2 and clean_word.isdigit() and len(clean_word) >= 3:
            # Keep model numbers / numbers like 15 (e.g. iphone 15) or 302
            tokens.add(clean_word)
            
    return tokens


def calculate_jaccard_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """
    Computes Jaccard similarity score from 0.0 to 100.0.
    J(A, B) = |A ∩ B| / |A ∪ B| * 100.
    If either set is empty, returns 0.0.
    """
    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)

    if not union:
        return 0.0

    return (len(intersection) / len(union)) * 100.0
