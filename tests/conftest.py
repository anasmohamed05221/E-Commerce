import os
os.environ["ENV"] = "testing"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from utils.hashing import get_password_hash
from services.token import TokenService
from models.users import User
from models.categories import Category
from models.products import Product
from models.enums import UserRole
from services.cart import CartService
from services.checkout import CheckoutService
from main import app
from core.database import Base
from core.config import settings
from utils.deps import get_db
from unittest.mock import AsyncMock
from core.redis_client import redis_client
from filelock import FileLock


# SYNC PostgreSql for testing (matches sync service layer)
SQLALCHEMY_DATABASE_URL = settings.TEST_DATABASE_URL

@pytest.fixture(scope="session")
def db_engine(tmp_path_factory, worker_id):
    """
    (Transactional isolation + xdist parallelism setup for testing time +60% optimization)
    Creates the database schema once for the entire test session.
    Drops all tables after all tests finish.
    """
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    if worker_id == "master":
        # Running without xdist — just create normally
        Base.metadata.create_all(bind=engine)
        yield engine
        Base.metadata.drop_all(bind=engine)
        return
    
    # Running with xdist — use a file lock so only one worker runs DDL
    root_tmp = tmp_path_factory.getbasetemp().parent
    lock_path = root_tmp / "db_setup.lock"
    flag_path = root_tmp / "db_ready.flag"

    with FileLock(str(lock_path)):
        if not flag_path.exists():
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            flag_path.touch()

    yield engine
    # No drop here — last worker can't reliably know it's last
    # Drop happens on next run's create_all (drop_all above)

    
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False)

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
def session(db_engine):
    """
    Wraps each test in a transaction with a savepoint.
    Rolls back after the test so data never persists between tests.
    Schema is reused across all tests — no create/drop per test.
    """
    connection = db_engine.connect()
    outer_transaction = connection.begin()
    
    # Create session
    db = TestingSessionLocal(bind=connection)
    db.begin_nested() # start first savepoint

    @event.listens_for(db, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield db

    db.close()
    outer_transaction.rollback()
    connection.close()


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


# Pre-hash once outside the fixture
HASHED_TEST_PASSWORD = get_password_hash("TestPassword123!")


@pytest.fixture
def verified_user(session, worker_id):
    """Create a verified, active user."""

    user = User(
        email=f"exampleuser_{worker_id}@email.com",
        first_name="Example",
        last_name="User",
        hashed_password=HASHED_TEST_PASSWORD,
        phone_number="+201111111111",
        is_verified=True,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def verified_admin(session, worker_id):
    """Create a verified, active admin."""

    user = User(
        email=f"exampleadmin_{worker_id}@email.com",
        first_name="Example",
        last_name="Admin",
        hashed_password=HASHED_TEST_PASSWORD,
        role=UserRole.ADMIN,
        phone_number="+2012121212121",
        is_verified=True,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def user_token(verified_user) -> str:
    """Generate a JWT access token for verified_user directly, bypassing HTTP login."""
    return TokenService.create_access_token(
        email=verified_user.email,
        user_id=verified_user.id,
        role=verified_user.role
    )


@pytest.fixture
def admin_token(verified_admin) -> str:
    """Generate a JWT access token for verified_admin directly, bypassing HTTP login."""
    return TokenService.create_access_token(
        email=verified_admin.email,
        user_id=verified_admin.id,
        role=verified_admin.role
    )


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