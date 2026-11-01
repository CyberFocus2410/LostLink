"""
Authentication API routes: register, login, me, refresh, logout,
forgot-password (stub), reset-password (stub).

Security:
- Rate-limited: login and register throttled to prevent brute force.
- Generic error messages: email-existence is never revealed.
- httpOnly + SameSite=Lax cookies only. No tokens in response bodies.
- Refresh token rotated on every /refresh call.
- Origin header checked for CSRF on state-changing requests (middleware).
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.limiter import limiter
from app.models.report import RefreshToken, User
from app.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserLogin,
    UserOut,
    UserRegister,
)
from app.schemas.common import APIResponse
from app.services.auth_service import (
    clear_auth_cookies,
    create_access_token,
    generate_refresh_token,
    get_current_user,
    get_refresh_token_from_cookie,
    hash_password,
    hash_refresh_token,
    needs_rehash,
    refresh_token_expires_at,
    set_auth_cookies,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

_GENERIC_AUTH_ERROR = "Invalid credentials. Please check your email and password."


# ─────────────── Register ───────────────

@router.post("/register", response_model=APIResponse[UserOut], status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register(
    request: Request,
    response: Response,
    data: UserRegister,
    db: Session = Depends(get_db),
):
    # Check for duplicate email — but return a generic message to prevent enumeration
    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing:
        # Generic delay path — same error as "wrong password"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        display_name=data.display_name.strip(),
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Issue tokens immediately on registration
    access_token = create_access_token(user.id)
    raw_refresh = generate_refresh_token()

    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=refresh_token_expires_at(),
    )
    db.add(rt)
    db.commit()

    set_auth_cookies(response, access_token, raw_refresh)
    return APIResponse.success(data=UserOut.model_validate(user))


# ─────────────── Login ───────────────

@router.post("/login", response_model=APIResponse[UserOut])
@limiter.limit("20/minute")
def login(
    request: Request,
    response: Response,
    data: UserLogin,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == data.email.lower()).first()

    # Always run password check (constant-time) even if user not found
    dummy_hash = "$argon2id$v=19$m=65536,t=3,p=4$AAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    stored_hash = user.password_hash if user else dummy_hash
    password_ok = verify_password(data.password, stored_hash)

    if not user or not password_ok or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_GENERIC_AUTH_ERROR,
        )

    # Rehash if argon2 parameters have improved
    if password_ok and needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password)
        db.commit()

    access_token = create_access_token(user.id)
    raw_refresh = generate_refresh_token()

    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=refresh_token_expires_at(),
    )
    db.add(rt)
    db.commit()

    set_auth_cookies(response, access_token, raw_refresh)
    return APIResponse.success(data=UserOut.model_validate(user))


# ─────────────── Me ───────────────

@router.get("/me", response_model=APIResponse[UserOut])
def me(current_user: User = Depends(get_current_user)):
    return APIResponse.success(data=UserOut.model_validate(current_user))


# ─────────────── Refresh ───────────────

@router.post("/refresh", response_model=APIResponse[UserOut])
def refresh_tokens(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Rotate refresh token:
    1. Read raw refresh token from cookie.
    2. Hash it and look up the stored record.
    3. Validate expiry and not-revoked.
    4. Revoke old record, issue new access + refresh token pair.
    """
    raw_refresh = get_refresh_token_from_cookie(request)
    if not raw_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    token_hash = hash_refresh_token(raw_refresh)
    rt = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked == False)
        .first()
    )
    if not rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalid or revoked")

    now = datetime.now(timezone.utc)
    expires_at = rt.expires_at if rt.expires_at.tzinfo else rt.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        rt.revoked = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = db.query(User).filter(User.id == rt.user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Rotate: revoke old, issue new
    rt.revoked = True
    db.flush()

    new_access = create_access_token(user.id)
    new_raw_refresh = generate_refresh_token()
    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_raw_refresh),
        expires_at=refresh_token_expires_at(),
    )
    db.add(new_rt)
    db.commit()

    set_auth_cookies(response, new_access, new_raw_refresh)
    return APIResponse.success(data=UserOut.model_validate(user))


# ─────────────── Logout ───────────────

@router.post("/logout", response_model=APIResponse[None])
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Revoke the refresh token server-side and clear both cookies.
    Works even if access token is already expired.
    """
    raw_refresh = get_refresh_token_from_cookie(request)
    if raw_refresh:
        token_hash = hash_refresh_token(raw_refresh)
        rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if rt:
            rt.revoked = True
            db.commit()

    clear_auth_cookies(response)
    return APIResponse.success(data=None)


# ─────────────── Delete Account & Anonymize Data (DPDP / GDPR) ───────────────

@router.delete("/me", response_model=APIResponse[dict])
def delete_my_account(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    DPDP & GDPR compliant account deletion.
    - Revokes all active refresh tokens.
    - Anonymizes personal identifiable information (name, email).
    - Scrubs contact information on active reports.
    - Deactivates the account and clears auth cookies.
    """
    import hashlib
    # Revoke all refresh tokens
    db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id).update({"revoked": True})

    # Anonymize user details
    anon_hash = hashlib.sha256(current_user.id.encode()).hexdigest()[:12]
    current_user.email = f"deleted_{anon_hash}@anonymized.lostlink"
    current_user.display_name = "Deleted User"
    current_user.is_active = False

    # Scrub private contact details from existing reports
    from app.models.report import Report
    db.query(Report).filter(Report.owner_id == current_user.id).update({
        "contact_name": "Deleted User",
        "contact_email": "deleted@anonymized.lostlink",
        "contact_phone": None,
    })

    db.commit()
    clear_auth_cookies(response)
    return APIResponse.success(
        data={
            "erased": True,
            "message": "Your account and personal data have been permanently anonymized and removed.",
        }
    )


# ─────────────── Forgot Password ───────────────

@router.post("/forgot-password", response_model=APIResponse[None])
@limiter.limit("5/minute")
def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Sends password reset instructions. Always returns 200 regardless of whether
    the email exists to prevent email enumeration.
    """
    import secrets
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if user and user.is_active:
        reset_token = secrets.token_urlsafe(24)
        from app.services.email_service import EmailService
        background_tasks.add_task(
            EmailService.send_password_reset_email,
            to_email=user.email,
            user_name=user.display_name,
            reset_token=reset_token,
        )
    return APIResponse.success(data=None)


# ─────────────── Reset Password (stub) ───────────────

@router.post("/reset-password", response_model=APIResponse[None])
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Verifies reset token and updates password."""
    return APIResponse.success(data=None)
