"""
LostLink Backend Configuration.
Centralized settings for database, weights, auth, and server parameters.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Settings:
    BASE_DIR: Path = BASE_DIR
    ENV: str = os.getenv("ENV", "development")
    APP_NAME: str = os.getenv("APP_NAME", "LostLink")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "t")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "127.0.0.1")
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:8000")

    # Database: default sqlite in backend root directory
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'lostlink.db'}")

    # CORS origins (supports CORS_ORIGINS or ALLOWED_ORIGINS)
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"),
        ).split(",")
        if origin.strip()
    ]

    # --- JWT / Auth ---
    # Generate with: openssl rand -hex 32
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_BEFORE_PRODUCTION_LOSTLINK_SECRET_KEY_MIN_32_BYTES")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Minimum password requirements
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))

    # Cookie domain (leave empty for localhost; set to your domain in prod)
    COOKIE_DOMAIN: str = os.getenv("COOKIE_DOMAIN", "")
    # In production, set COOKIE_SECURE=true so cookies are Secure
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() in ("true", "1", "t")

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

    # --- Storage Configuration (Phase 6) ---
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "supabase").lower()
    STORAGE_LOCAL_DIR: Path = Path(os.getenv("STORAGE_LOCAL_DIR", str(BASE_DIR / "uploads")))
    STORAGE_MAX_FILE_SIZE_BYTES: int = int(os.getenv("STORAGE_MAX_FILE_SIZE_BYTES", str(5 * 1024 * 1024)))  # 5 MB
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_PUBLISHABLE_KEY: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv(
        "SUPABASE_SERVICE_ROLE_KEY",
        os.getenv("SUPABASE_SECRET_KEY", "")
    )
    SUPABASE_JWKS_URL: str = os.getenv("SUPABASE_JWKS_URL", "")
    SUPABASE_STORAGE_BUCKET: str = os.getenv("SUPABASE_STORAGE_BUCKET", "lostlink-images")

    # --- Email Configuration (Phase 7) ---
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "resend").lower()
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "onboarding@resend.dev")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # --- Monitoring & Analytics (Phase 9) ---
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "true").lower() in ("true", "1", "t")


settings = Settings()
