"""
LostLink Backend Application Entrypoint.
FastAPI setup with CORS, CSRF middleware, slowapi rate limiting,
lifespan startup indexing, consistent exception handlers, and routing.
"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api import api_router
from app.schemas.common import APIResponse
from app.services.report_service import ReportService
from app.middleware.csrf import CSRFOriginMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.limiter import limiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("LostLink")

# Initialize Sentry error monitoring if configured
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENV,
            traces_sample_rate=0.1 if settings.ENV == "production" else 1.0,
            send_default_pii=False,
        )
        logger.info("Sentry error monitoring initialized.")
    except ImportError:
        logger.warning("sentry-sdk not installed; skipping Sentry initialization.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database initialization and index warming."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # Rebuild in-memory DSA indexes from DB to preserve persistence across restarts
    db = SessionLocal()
    try:
        count = ReportService.rebuild_all_indexes(db)
        logger.info(f"Loaded and indexed {count} reports from database.")
    except Exception as e:
        logger.error(f"Error rebuilding in-memory index on startup: {e}")
    finally:
        db.close()

    yield

    logger.info("LostLink backend shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Deterministic Smart Lost & Found Matcher API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach slowapi limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware — must be added before CSRF so preflight OPTIONS pass
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSRF Origin-check middleware — after CORS so OPTIONS is already handled
app.add_middleware(CSRFOriginMiddleware)

# Security Headers (CSP, nosniff, DENY, Referrer-Policy)
app.add_middleware(SecurityHeadersMiddleware)


# ─────────── Standard error envelopes ───────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    field_errors = {}
    for err in exc.errors():
        field_name = ".".join(str(loc) for loc in err["loc"] if loc != "body")
        field_errors[field_name] = err["msg"]

    envelope = APIResponse.fail(
        code="VALIDATION_ERROR",
        message="Please correct the highlighted fields.",
        fields=field_errors,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=envelope.model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        503: "SERVICE_UNAVAILABLE",
    }
    error_code = code_map.get(exc.status_code, "ERROR")
    envelope = APIResponse.fail(code=error_code, message=str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=envelope.model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    envelope = APIResponse.fail(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred. Please try again later.",
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=envelope.model_dump(),
    )


from fastapi.staticfiles import StaticFiles

# Ensure upload directory exists and mount static serving for uploads
settings.STORAGE_LOCAL_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=str(settings.STORAGE_LOCAL_DIR)), name="static_uploads")

# Mount API routes
app.include_router(api_router)

# ─────────── Single-Service Static & SPA Serving (Production) ───────────
from starlette.responses import FileResponse

# Check for built frontend in parent or in container working directory
frontend_candidates = [
    settings.BASE_DIR.parent / "frontend" / "dist",
    Path("/app/frontend/dist"),
    settings.BASE_DIR / "static" / "frontend",
]

frontend_dist = next((p for p in frontend_candidates if p.exists()), None)

if frontend_dist:
    logger.info(f"Mounting built SPA frontend from: {frontend_dist}")
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="spa_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa_frontend(request: Request, full_path: str):
        if full_path.startswith("api") or full_path.startswith("static"):
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = frontend_dist / full_path
        if target_file.is_file():
            return FileResponse(target_file)
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")

