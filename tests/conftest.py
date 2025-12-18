import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

# Main app dependencies
from main import app
from core.database import Base
from utils.deps import get_db
from core.config import settings

# CONFIGURE TEST DATABASE
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates a fresh, empty database for each test.
    """
    # Create all tables in the test DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Yield a session connected to this fresh DB
    async with TestingSessionLocal() as session:
        yield session

    # TEARDOWN: Drop all tables after the test completes
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Yields an HTTP client that interacts with the app using the test database.
    """
    # Define an override that returns our test session fixture
    async def override_get_db():
        yield session
    # Apply the override to the app
    app.dependency_overrides[get_db] = override_get_db
    # Create the AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    # Clean up: remove the override so we don't affect other things
    app.dependency_overrides.clear()