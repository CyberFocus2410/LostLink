"""
LostLink Backend Configuration.
Centralized settings for database, weights, and server parameters.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings:
    ENV: str = os.getenv("ENV", "development")
    APP_NAME: str = os.getenv("APP_NAME", "LostLink")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "t")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "127.0.0.1")

    # Database: default sqlite in backend root directory
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'lostlink.db'}")

    # CORS origins
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
        ).split(",")
        if origin.strip()
    ]

    # Matching Weights (Heuristic ranking weights, NOT probabilities)
    # Total Score S = 0.35C + 0.25L + 0.20D + 0.20K (Heuristic 0.0 - 1.0)
    # NOTE: These values are empirical ranking heuristics for campus items,
    # not statistical probabilities of identity or ownership proof.
    WEIGHT_CATEGORY: float = float(os.getenv("WEIGHT_CATEGORY", "0.35"))
    WEIGHT_LOCATION: float = float(os.getenv("WEIGHT_LOCATION", "0.25"))
    WEIGHT_DATE: float = float(os.getenv("WEIGHT_DATE", "0.20"))
    WEIGHT_KEYWORD: float = float(os.getenv("WEIGHT_KEYWORD", "0.20"))

    # Decay: D = max(0, 100 - DATE_DECAY_RATE * absolute_days)
    DATE_DECAY_RATE: float = float(os.getenv("DATE_DECAY_RATE", "15.0"))

    # Configurable candidate window: reports farther than this window are excluded
    CANDIDATE_DATE_WINDOW_DAYS: int = int(os.getenv("CANDIDATE_DATE_WINDOW_DAYS", "30"))
    MINIMUM_MATCH_SCORE: float = float(os.getenv("MINIMUM_MATCH_SCORE", "20.0"))

settings = Settings()

