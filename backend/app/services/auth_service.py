"""
Auth service: password hashing (argon2), JWT access tokens (PyJWT),
refresh token creation/rotation/revocation, and cookie helpers.

Security design:
- Access token: JWT, 15-min TTL, signed HS256, delivered in httpOnly cookie.
- Refresh token: 32-byte random secret, 7-day TTL, SHA-256 hash stored server-side.
  Rotated on every use. Logout deletes the stored hash → true revocation.
- CSRF protection: Origin header checked on state-changing requests in middleware.
- Passwords: argon2id via argon2-cffi. Never bcrypt or plaintext.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

_ph = PasswordHasher()

# ────────────────────────── Password hashing ──────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plaintext password with argon2id."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches hashed; False on any mismatch."""
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    """Check if stored hash needs upgrading to current argon2 parameters."""
    return _ph.check_needs_rehash(hashed)


# ────────────────────────── JWT access tokens ──────────────────────────

def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": secrets.token_hex(16),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate JWT. Raises HTTPException 401 on any failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")


# ────────────────────────── Refresh tokens ──────────────────────────

def generate_refresh_token() -> str:
    """Return a cryptographically random 32-byte URL-safe token (raw value, never stored)."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(raw: str) -> str:
    """SHA-256 hex digest of the raw refresh token — this is what goes into the DB."""
    return hashlib.sha256(raw.encode()).hexdigest()


def refresh_token_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


# ────────────────────────── Cookie helpers ──────────────────────────

_ACCESS_COOKIE = "lostlink_access"
_REFRESH_COOKIE = "lostlink_refresh"


def _get_cookie_domain() -> Optional[str]:
    cd = settings.COOKIE_DOMAIN.strip() if settings.COOKIE_DOMAIN else ""
    # Only use domain if it contains a valid dot-separated host and isn't a hex container id
    if cd and "." in cd and not cd.startswith("localhost") and not cd.endswith(".local") and len(cd) < 50:
        return cd
    return None


def set_auth_cookies(response, access_token: str, refresh_token: str) -> None:
    """Write both tokens as httpOnly cookies on the response object."""
    domain = _get_cookie_domain()
    common = dict(
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        domain=domain,
    )
    response.set_cookie(
        key=_ACCESS_COOKIE,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        **common,
    )
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
        **common,
    )


def clear_auth_cookies(response) -> None:
    """Expire both cookies immediately."""
    domain = _get_cookie_domain()
    common = dict(
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        domain=domain,
    )
    response.delete_cookie(key=_ACCESS_COOKIE, path="/", **common)
    response.delete_cookie(key=_REFRESH_COOKIE, path="/", **common)
    response.delete_cookie(key=_REFRESH_COOKIE, path="/api/auth", **common)


# ────────────────────────── FastAPI dependencies ──────────────────────────

def get_access_token_from_cookie(request: Request) -> Optional[str]:
    return request.cookies.get(_ACCESS_COOKIE)


def get_refresh_token_from_cookie(request: Request) -> Optional[str]:
    return request.cookies.get(_REFRESH_COOKIE)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency: reads access-token cookie, validates JWT, returns User ORM object.
    Raises HTTP 401 if missing or invalid.
    """
    from app.models.report import User  # local import to avoid circular at module load

    token = get_access_token_from_cookie(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
        )
    payload = decode_access_token(token)
    user_id: str = payload["sub"]

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or deactivated.",
        )
    return user


def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Like get_current_user but returns None instead of raising when not authenticated.
    Used on public routes that behave differently for authenticated users.
    """
    from app.models.report import User

    token = get_access_token_from_cookie(request)
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id: str = payload["sub"]
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()
    except HTTPException:
        return None


def require_admin(
    current_user=Depends(get_current_user),
):
    """
    FastAPI dependency: verifies current authenticated user has 'admin' or 'moderator' role.
    Raises 403 Forbidden otherwise.
    """
    if current_user.role not in ("admin", "moderator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or moderator privileges required.",
        )
    return current_user

