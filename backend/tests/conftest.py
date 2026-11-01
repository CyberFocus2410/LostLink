"""
Pytest configuration and fixtures with isolated test database using StaticPool.

Existing 25 tests use anonymous report creation (no auth required).
The create-report route is protected, so we override get_current_user
with a mock user fixture for those tests.
New auth tests create their own users via the register endpoint.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from datetime import datetime, timezone
from app.database import Base, get_db
from app.main import app
from app.matching.index import matching_index
from app.services.auth_service import get_current_user
from app.limiter import limiter

# In-memory SQLite with StaticPool so all threads share the exact same in-memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class _MockUser:
    """Minimal user object satisfying the get_current_user dependency for existing tests."""
    id = "00000000-test-0000-0000-000000000000"
    display_name = "Test User"
    email = "test@example.com"
    role = "user"
    is_active = True
    created_at = datetime.now(timezone.utc)


_MOCK_USER = _MockUser()


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database tables for each test and tear down after."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    matching_index.clear()
    limiter.reset()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        matching_index.clear()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db and get_current_user dependencies."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return _MOCK_USER

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def real_auth_client(db_session):
    """TestClient that uses real auth (no get_current_user override)."""
    limiter.reset()
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
