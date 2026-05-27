import pytest
from models.tenants import Tenant
from models.categories import Category
from tests.conftest import HASHED_TEST_PASSWORD
import hashlib


@pytest.fixture
async def second_tenant(session, worker_id):
    """Create a second tenant for cross-tenant isolation tests."""
    tenant = Tenant(
        name="Second Test Store",
        owner_email=f"second_tenant_owner_{worker_id}@test.com",
        owner_password_hash=HASHED_TEST_PASSWORD,
        slug=f"second-test-store-{worker_id}",
        api_key_hash=hashlib.sha256(f"second-test-api-key-{worker_id}".encode()).hexdigest(),
    )
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)
    tenant._plaintext_api_key = f"second-test-api-key-{worker_id}"
    return tenant


@pytest.fixture
async def second_category(session, second_tenant):
    """A category belonging to the second tenant."""
    category = Category(tenant_id=second_tenant.id, name="Electronics", description="Tech gear")
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category