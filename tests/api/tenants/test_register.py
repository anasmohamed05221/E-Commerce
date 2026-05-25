import hashlib
from sqlalchemy import select, func
from models.tenants import Tenant

VALID_PAYLOAD = {
    "name": "Acme Store",
    "slug": "acme-store",
    "email": "owner@acme.com",
    "password": "SecurePass123!"
}


async def test_register_success(client, session):
    """Happy path: tenant created, API key returned once, hash stored in DB."""
    response = await client.post("/tenants/register", json=VALID_PAYLOAD)

    assert response.status_code == 201
    data = response.json()

    # Response shape
    assert data["name"] == "Acme Store"
    assert data["slug"] == "acme-store"
    assert data["plan"] == "free"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data

    # API key format: vnx_ prefix + 43 base64url chars = 47 total
    api_key = data["api_key"]
    assert api_key.startswith("vnx_")
    assert len(api_key) == 47

    # DB: tenant row exists with correct fields
    tenant = await session.scalar(select(Tenant).where(Tenant.slug == "acme-store"))
    assert tenant is not None
    assert tenant.name == "Acme Store"
    assert tenant.is_active is True

    # DB: api_key_hash is SHA256 of the returned plaintext — never stored directly
    expected_hash = hashlib.sha256(api_key.encode()).hexdigest()
    assert tenant.api_key_hash == expected_hash
    assert len(tenant.api_key_hash) == 64
    assert tenant.api_key_hash != api_key

    # DB: password is hashed, never plaintext
    assert tenant.owner_password_hash != "SecurePass123!"

    # Response: no sensitive fields leaked
    assert "owner_password_hash" not in data
    assert "api_key_hash" not in data


async def test_register_default_plan_is_free(client, session):
    """Plan defaults to FREE when omitted from the request."""
    payload = {**VALID_PAYLOAD, "slug": "no-plan-store"}

    response = await client.post("/tenants/register", json=payload)
    assert response.status_code == 201

    tenant = await session.scalar(select(Tenant).where(Tenant.slug == "no-plan-store"))
    assert tenant.plan.value == "free"


async def test_register_duplicate_slug(client, session):
    """Duplicate slug returns 409 and only one tenant row is persisted."""
    await client.post("/tenants/register", json={**VALID_PAYLOAD, "slug": "dup-slug"})
    response = await client.post("/tenants/register", json={**VALID_PAYLOAD, "slug": "dup-slug", "email": "other@acme.com"})

    assert response.status_code == 409

    count = await session.scalar(
        select(func.count()).select_from(Tenant).where(Tenant.slug == "dup-slug")
    )
    assert count == 1


async def test_register_same_email_multiple_tenants(client, session):
    """Same owner email can register multiple tenants (multi-store owner support)."""
    r1 = await client.post("/tenants/register", json={**VALID_PAYLOAD, "slug": "store-one"})
    r2 = await client.post("/tenants/register", json={**VALID_PAYLOAD, "slug": "store-two"})

    assert r1.status_code == 201
    assert r2.status_code == 201

    count = await session.scalar(
        select(func.count()).select_from(Tenant).where(Tenant.owner_email == VALID_PAYLOAD["email"])
    )
    assert count == 2


async def test_register_invalid_slug_leading_hyphen(client, session):
    """Slug starting with a hyphen fails regex validation and no row is created."""
    response = await client.post("/tenants/register", json={**VALID_PAYLOAD, "slug": "-bad-slug"})

    assert response.status_code == 422

    tenant = await session.scalar(select(Tenant).where(Tenant.slug == "-bad-slug"))
    assert tenant is None


async def test_register_invalid_slug_uppercase(client, session):
    """Uppercase slug fails regex validation."""
    response = await client.post("/tenants/register", json={**VALID_PAYLOAD, "slug": "UPPERCASE"})

    assert response.status_code == 422


async def test_register_slug_too_short(client, session):
    """Slug shorter than 3 characters fails validation."""
    response = await client.post("/tenants/register", json={**VALID_PAYLOAD, "slug": "ab"})

    assert response.status_code == 422


async def test_register_name_too_long(client, session):
    """Name exceeding 100 characters fails validation and no row is created."""
    response = await client.post("/tenants/register", json={**VALID_PAYLOAD, "name": "a" * 101})

    assert response.status_code == 422

    tenant = await session.scalar(select(Tenant).where(Tenant.slug == VALID_PAYLOAD["slug"]))
    assert tenant is None


async def test_register_invalid_plan(client, session):
    """Unknown plan value returns 422."""
    response = await client.post("/tenants/register", json={**VALID_PAYLOAD, "plan": "gold"})

    assert response.status_code == 422


async def test_register_missing_required_fields(client, session):
    """Request missing slug returns 422."""
    payload = {"name": "Acme Store", "email": "owner@acme.com", "password": "SecurePass123!"}

    response = await client.post("/tenants/register", json=payload)

    assert response.status_code == 422


async def test_register_weak_password(client, session):
    """Weak password fails validation and no row is created."""
    response = await client.post("/tenants/register", json={**VALID_PAYLOAD, "password": "weak"})

    assert response.status_code == 422

    tenant = await session.scalar(select(Tenant).where(Tenant.slug == VALID_PAYLOAD["slug"]))
    assert tenant is None
