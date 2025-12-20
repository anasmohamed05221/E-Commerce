import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from main import app
from core.database import Base
from utils.deps import get_db

# SYNC SQLite for testing (matches sync service layer)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """
    Creates a fresh, empty database for each test.
    Uses SYNC SQLAlchemy to match the service layer.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    
    # Drop all tables (cleanup)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
async def client(session: Session):
    """
    Yields an HTTP client that interacts with the app using the test database.
    The client is async (for FastAPI), but the DB session is sync.
    """
    # Override the get_db dependency to use our test session
    def override_get_db():
        try:
            yield session
        finally:
            pass  # Session cleanup handled by session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create async client for FastAPI
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    # Clean up
    app.dependency_overrides.clear()