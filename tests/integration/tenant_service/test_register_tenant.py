import hashlib
import pytest
from sqlalchemy import select, func
from fastapi import HTTPException
from models.tenants import Tenant
from models.enums import PlanTier
from services.tenants import TenantService


VALID_ARGS = {
    "name": "Acme Store",
    "slug": "acme-store",
    "email": "owner@acme.com",
    "password": "SecurePass123!",
    "plan": PlanTier.FREE,
}


async def test_register_tenant_persists_correct_db_state(session):
    """Happy path: tenant row exists with correct fields and hashed credentials."""
    tenant, api_key = await TenantService.register_tenant(session, **VALID_ARGS)

    db_tenant = await session.scalar(select(Tenant).where(Tenant.slug == "acme-store"))
    assert db_tenant is not None
    assert db_tenant.name == "Acme Store"
    assert db_tenant.owner_email == "owner@acme.com"
    assert db_tenant.plan == PlanTier.FREE
    assert db_tenant.is_active is True
    assert db_tenant.id is not None
    assert db_tenant.created_at is not None


async def test_register_tenant_cryptographic_contract(session):
    """api_key_hash stored in DB must equal SHA256 of the returned plaintext key."""
    tenant, api_key = await TenantService.register_tenant(session, **VALID_ARGS)

    db_tenant = await session.scalar(select(Tenant).where(Tenant.slug == "acme-store"))
    expected_hash = hashlib.sha256(api_key.encode()).hexdigest()
    assert db_tenant.api_key_hash == expected_hash
    assert len(db_tenant.api_key_hash) == 64
    assert db_tenant.api_key_hash != api_key


async def test_register_tenant_password_is_hashed(session):
    """owner_password_hash stored in DB must be a bcrypt hash, never plaintext."""
    tenant, api_key = await TenantService.register_tenant(session, **VALID_ARGS)

    db_tenant = await session.scalar(select(Tenant).where(Tenant.slug == "acme-store"))
    assert db_tenant.owner_password_hash != "SecurePass123!"
    assert db_tenant.owner_password_hash.startswith("$2b$")


async def test_register_tenant_duplicate_slug_raises_409(session):
    """Duplicate slug raises HTTPException 409 and only one row is persisted."""
    await TenantService.register_tenant(session, **VALID_ARGS)

    with pytest.raises(HTTPException) as exc_info:
        await TenantService.register_tenant(
            session, **{**VALID_ARGS, "email": "other@acme.com"}
        )

    assert exc_info.value.status_code == 409

    count = await session.scalar(
        select(func.count()).select_from(Tenant).where(Tenant.slug == "acme-store")
    )
    assert count == 1


async def test_register_tenant_same_email_multiple_tenants(session):
    """Same owner email can register multiple tenants -- non-unique by design."""
    await TenantService.register_tenant(session, **{**VALID_ARGS, "slug": "store-one"})
    await TenantService.register_tenant(session, **{**VALID_ARGS, "slug": "store-two"})

    count = await session.scalar(
        select(func.count()).select_from(Tenant).where(Tenant.owner_email == VALID_ARGS["email"])
    )
    assert count == 2
