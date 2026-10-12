"""
LostLink Backend Application Entrypoint.
FastAPI setup with CORS, lifespan startup indexing, consistent exception handlers, and routing.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api import api_router
from app.schemas.common import APIResponse
from app.services.report_service import ReportService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("LostLink")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database initialization and index warming."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # Rebuild in-memory DSA indexes from SQLite to preserve persistence across restarts
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
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Standard Error Envelopes
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


# Mount routes
app.include_router(api_router)
