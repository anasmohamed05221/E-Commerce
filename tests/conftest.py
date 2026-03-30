import os
os.environ["ENV"] = "testing"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from utils.hashing import get_password_hash
from models.users import User
from models.categories import Category
from models.products import Product
from services.cart import CartService
from services.checkout import CheckoutService
from main import app
from core.database import Base
from core.config import settings
from utils.deps import get_db
from unittest.mock import AsyncMock
from core.redis_client import redis_client

# SYNC PostgreSql for testing (matches sync service layer)
SQLALCHEMY_DATABASE_URL = settings.TEST_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture(autouse=True)
def mock_redis_for_tests():
    """
    Automatically intercept the redis client before EVERY test.
    We inject a fake 'AsyncMock' object that simulates a Cache Miss
    so the tests always hit the SQLite test database smoothly.
    """
    # Create a fake redis object
    fake_redis = AsyncMock()
    # Tell the fake .get() method to return None (Cache Miss)
    fake_redis.get.return_value = None
    
    # Temporarily attach it to your application's redis_client
    redis_client.redis = fake_redis
    
    yield  # Let the test run!
    
    # Cleanup after the test finishes
    redis_client.redis = None

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



@pytest.fixture
def verified_user(session):
    """Create a verified, active user for testing authentication."""

    user = User(
        email="exampleuser@email.com",
        first_name="Example",
        last_name="User",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111111",
        is_verified=True,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def test_category(session):
    """Create a reusable test category."""
    category = Category(name="Electronics", description="Tech gear")
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@pytest.fixture
def product_factory(session, test_category):
    """Factory fixture to create test products with custom attributes."""
    def _create(*, name="Laptop", price=1000.00, stock=10):
        product = Product(name=name, price=price, stock=stock, category_id=test_category.id)
        session.add(product)
        session.commit()
        session.refresh(product)
        return product
    return _create


@pytest.fixture
def seed_products(session, test_category):
    """Seed multiple products for API testing."""
    p1 = Product(name="Laptop", price=1000.00, stock=5, category_id=test_category.id)
    p2 = Product(name="Mouse", price=50.00, stock=20, category_id=test_category.id)

    session.add_all([p1, p2])
    session.commit()

    # Return so tests can access their IDs
    return [p1, p2]


@pytest.fixture
def order_factory(session, verified_user, product_factory):
    def _create(products_and_quantities=None):
        if products_and_quantities is None:
            products_and_quantities = [(product_factory(), 2)]
        for product, quantity in products_and_quantities:
            CartService.add_to_cart(session, verified_user.id, product.id, quantity)
        
        return CheckoutService.checkout(session, verified_user.id)
    return _create