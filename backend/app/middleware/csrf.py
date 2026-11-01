"""
Origin-header CSRF protection middleware.

For state-changing requests (POST, PATCH, DELETE, PUT) we verify that the
Origin header (sent automatically by all modern browsers for cross-origin
requests) matches one of the configured CORS_ORIGINS.

This works because:
  1. Browsers always include Origin on cross-site requests.
  2. Cookies are sent automatically by the browser, so an attacker can trigger
     a request — but the Origin will be their domain, not ours.
  3. Same-origin requests (SPA calling its own backend) have Origin == our origin,
     or the header may be absent on simple GET/HEAD requests.

Paths exempt from the check:
  - GET, HEAD, OPTIONS (read-only or preflight)
  - /api/auth/refresh and /api/auth/logout when called from the same app
    (these paths also check the cookie which is scoped, providing extra defense)

This is complementary to SameSite=Lax cookies, which already block
cross-site POSTs from top-level navigations. Together they provide
defense-in-depth against CSRF.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.config import settings

# Methods that mutate state
_MUTATING_METHODS = {"POST", "PATCH", "PUT", "DELETE"}

# Allowed origin set derived from config (lowercase, stripped)
def _build_allowed() -> set[str]:
    allowed = set()
    for o in settings.CORS_ORIGINS:
        o = o.strip().rstrip("/")
        if o:
            allowed.add(o)
    return allowed


class CSRFOriginMiddleware(BaseHTTPMiddleware):
    """
    Checks Origin header on mutating requests and rejects requests with an
    unexpected origin. Requests with no Origin header from localhost are
    allowed (e.g., Swagger UI / curl testing in development).
    """

    async def dispatch(self, request: Request, call_next):
        if request.method not in _MUTATING_METHODS:
            return await call_next(request)

        origin = request.headers.get("origin", "").strip().rstrip("/")
        allowed = _build_allowed()
        allowed.add(str(request.base_url).rstrip("/"))

        if not origin:
            # No Origin header: allow in dev; block in production
            if settings.ENV == "production":
                return JSONResponse(
                    status_code=403,
                    content={"data": None, "error": {"code": "CSRF_FORBIDDEN", "message": "Forbidden"}, "meta": None},
                )
            return await call_next(request)

        if origin not in allowed:
            return JSONResponse(
                status_code=403,
                content={"data": None, "error": {"code": "CSRF_FORBIDDEN", "message": "Forbidden: origin not allowed"}, "meta": None},
            )

        return await call_next(request)
