import os
os.environ["ENV"] = "testing"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "True"
import hashlib
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from utils.hashing import get_password_hash
from services.token import TokenService
from models.tenants import Tenant
from models.users import User
from models.categories import Category
from models.products import Product
from models.addresses import Address
from models.enums import UserRole, PaymentMethod
from services.cart import CartService
from services.checkout import CheckoutService
from main import app
from core.database import Base
from core.config import settings
from contextlib import asynccontextmanager
from utils.deps import get_db
import middleware.tenant_resolver as tenant_resolver_module
from unittest.mock import AsyncMock
from core.redis_client import redis_client
from filelock import FileLock


SQLALCHEMY_DATABASE_URL = settings.TEST_DATABASE_URL


@pytest.fixture(scope="session")
def worker_id(request):
    """Provide worker_id even when xdist is not active."""
    if hasattr(request.config, "workerinput"):
        return request.config.workerinput["workerid"]
    return "master"


# Engine & Schema (session-scoped, xdist-safe)

@pytest.fixture(scope="session")
async def db_engine(tmp_path_factory, worker_id):
    """Create the async engine and set up schema once per test session."""
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

    if worker_id == "master":
        # Running without xdist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
        return

    # Running with xdist -- file lock so only one worker creates tables
    root_tmp = tmp_path_factory.getbasetemp().parent
    lock_path = root_tmp / "db_setup.lock"
    flag_path = root_tmp / "db_ready.flag"

    with FileLock(str(lock_path)):
        if not flag_path.exists():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
            flag_path.touch()

    yield engine
    await engine.dispose()


# Transactional Isolation (per-test)
#
# How it works:
#   1. Each test gets its own CONNECTION with a BEGIN (outer transaction).
#   2. A SAVEPOINT sits inside that transaction.
#   3. When service code calls session.commit(), it releases the savepoint
#      (not the outer transaction). An event listener immediately opens a
#      new savepoint so the next commit is also contained.
#   4. After the test, the outer transaction is ROLLED BACK.
#      Nothing ever reaches the database, so each test starts with a clean state.

@pytest.fixture
async def connection(db_engine):
    """Per-test connection with an outer transaction that is always rolled back."""
    async with db_engine.connect() as conn:
        txn = await conn.begin()
        await conn.begin_nested()
        try:
            yield conn
        finally:
            await txn.rollback()


@pytest.fixture
async def session(connection):
    """Async session for test fixtures and assertions, bound to the shared connection."""
    async_session = AsyncSession(bind=connection, expire_on_commit=False)

    @event.listens_for(async_session.sync_session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if connection.closed:
            return
        if not connection.in_nested_transaction():
            connection.sync_connection.begin_nested()

    try:
        yield async_session
    finally:
        await async_session.close()


@pytest.fixture
async def client(connection, test_tenant):
    """
    HTTPX test client. Both get_db and the middleware's SessionLocal are overridden
    to share the test connection. The real TenantResolverMiddleware runs and resolves
    test_tenant via the X-Tenant-API-Key default header on every request.
    """
    async def override_get_db():
        async with AsyncSession(bind=connection, expire_on_commit=False) as db_session:
            db_session.info["tenant_id"] = test_tenant.id
            yield db_session

    @asynccontextmanager
    async def test_session_local():
        async with AsyncSession(bind=connection, expire_on_commit=False) as db_session:
            db_session.info["tenant_id"] = test_tenant.id
            yield db_session

    original_session_local = tenant_resolver_module.SessionLocal
    tenant_resolver_module.SessionLocal = test_session_local
    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Tenant-API-Key": test_tenant._plaintext_api_key}
        ) as ac:
            yield ac
    finally:
        tenant_resolver_module.SessionLocal = original_session_local
        app.dependency_overrides.clear()


# Redis Mock

HASHED_TEST_PASSWORD = get_password_hash("TestPassword123!")


@pytest.fixture(autouse=True)
def mock_redis_for_tests():
    """Mock Redis to always return cache miss so tests hit the database."""
    fake_redis = AsyncMock()
    fake_redis.get.return_value = None
    redis_client.redis = fake_redis
    yield
    redis_client.redis = None


# Tenant Fixture

@pytest.fixture
async def test_tenant(session, worker_id):
    """Create a test tenant for all model fixtures."""
    tenant = Tenant(
        name="Test Store",
        owner_email=f"tenant_owner_{worker_id}@test.com",
        owner_password_hash=HASHED_TEST_PASSWORD,
        slug=f"test-store-{worker_id}",
        api_key_hash=hashlib.sha256(f"test-api-key-{worker_id}".encode()).hexdigest(),
    )
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)
    session.info["tenant_id"] = tenant.id
    tenant._plaintext_api_key = f"test-api-key-{worker_id}"
    return tenant


# User Fixtures

@pytest.fixture
async def verified_user(session, worker_id, test_tenant):
    """Create a verified, active customer."""
    user = User(
        tenant_id=test_tenant.id,
        email=f"testuser_{worker_id}@email.com",
        first_name="Test",
        last_name="User",
        hashed_password=HASHED_TEST_PASSWORD,
        phone_number="+201111111111",
        is_verified=True,
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def verified_admin(session, worker_id, test_tenant):
    """Create a verified, active admin."""
    user = User(
        tenant_id=test_tenant.id,
        email=f"testadmin_{worker_id}@email.com",
        first_name="Test",
        last_name="Admin",
        hashed_password=HASHED_TEST_PASSWORD,
        role=UserRole.ADMIN,
        phone_number="+201212121212",
        is_verified=True,
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


# Token Fixtures

@pytest.fixture
def user_token(verified_user) -> str:
    """JWT access token for verified_user (no HTTP roundtrip)."""
    return TokenService.create_access_token(
        tenant_id=str(verified_user.tenant_id),
        email=verified_user.email,
        user_id=verified_user.id,
        role=verified_user.role
    )


@pytest.fixture
def admin_token(verified_admin) -> str:
    """JWT access token for verified_admin (no HTTP roundtrip)."""
    return TokenService.create_access_token(
        tenant_id=str(verified_admin.tenant_id),
        email=verified_admin.email,
        user_id=verified_admin.id,
        role=verified_admin.role
    )


# Data Fixtures

@pytest.fixture
async def test_category(session, test_tenant):
    """A reusable test category."""
    category = Category(tenant_id=test_tenant.id, name="Electronics", description="Tech gear")
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


@pytest.fixture
async def product_factory(session, test_category, test_tenant):
    """Factory to create products. Usage: product = await product_factory(name=..., stock=...)"""
    async def _create(*, name=None, price=1000.00, stock=10):
        name = name or f"Product-{uuid.uuid4().hex[:8]}"
        product = Product(tenant_id=test_tenant.id, name=name, price=price, stock=stock, category_id=test_category.id)
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product
    return _create


@pytest.fixture
async def seed_products(session, test_category, test_tenant):
    """Seed two products for listing/filter tests."""
    p1 = Product(tenant_id=test_tenant.id, name="Laptop", price=1000.00, stock=5, category_id=test_category.id)
    p2 = Product(tenant_id=test_tenant.id, name="Mouse", price=50.00, stock=20, category_id=test_category.id)
    session.add_all([p1, p2])
    await session.commit()
    return [p1, p2]


@pytest.fixture
async def test_address(session, verified_user, test_tenant):
    """Default address for verified_user."""
    address = Address(
        tenant_id=test_tenant.id,
        user_id=verified_user.id,
        street="123 Test St",
        city="Cairo",
        country="Egypt",
        postal_code="11511",
        is_default=True,
    )
    session.add(address)
    await session.commit()
    await session.refresh(address)
    return address


@pytest.fixture
async def order_factory(session, verified_user, product_factory, test_address, test_tenant):
    """Factory to create orders via the full checkout flow."""
    async def _create(products_and_quantities=None):
        if products_and_quantities is None:
            products_and_quantities = [(await product_factory(), 2)]
        for product, quantity in products_and_quantities:
            await CartService.add_to_cart(
                db=session, tenant_id=test_tenant.id, user_id=verified_user.id,
                product_id=product.id, quantity=quantity
            )
        return await CheckoutService.checkout(
            db=session, tenant_id=test_tenant.id, user_id=verified_user.id,
            address_id=test_address.id, payment_method=PaymentMethod.COD
        )
    return _create