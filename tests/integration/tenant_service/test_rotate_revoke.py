import hashlib
import pytest
from sqlalchemy import select
from fastapi import HTTPException
from models.tenants import Tenant
from services.tenants import TenantService
from core.redis_client import redis_client


async def test_rotate_api_key_updates_hash(session, test_tenant):
    """After rotation, DB api_key_hash must equal SHA256 of the returned plaintext key."""
    old_hash = test_tenant.api_key_hash

    new_plaintext = await TenantService.rotate_api_key(session, test_tenant)

    await session.refresh(test_tenant)
    expected_hash = hashlib.sha256(new_plaintext.encode()).hexdigest()
    assert test_tenant.api_key_hash == expected_hash
    assert test_tenant.api_key_hash != old_hash


async def test_rotate_api_key_plaintext_not_stored(session, test_tenant):
    """The returned plaintext key must never equal the stored hash, and hash must be 64-char hex."""
    new_plaintext = await TenantService.rotate_api_key(session, test_tenant)

    await session.refresh(test_tenant)
    assert test_tenant.api_key_hash != new_plaintext
    assert len(test_tenant.api_key_hash) == 64


async def test_rotate_api_key_invalidates_redis_cache(session, test_tenant):
    """Both tenant:apikey and tenant:id cache keys must be deleted from Redis after rotation."""
    await TenantService.rotate_api_key(session, test_tenant)

    assert redis_client.redis.delete.call_count == 2


async def test_revoke_api_key_sets_hash_to_null(session, test_tenant):
    """After revocation, api_key_hash in DB must be None."""
    await TenantService.revoke_api_key(session, test_tenant)

    await session.refresh(test_tenant)
    assert test_tenant.api_key_hash is None


async def test_revoke_api_key_tenant_stays_active(session, test_tenant):
    """Revoking the API key must not deactivate the tenant."""
    await TenantService.revoke_api_key(session, test_tenant)

    await session.refresh(test_tenant)
    assert test_tenant.is_active is True


async def test_revoke_already_revoked_raises_400(session, test_tenant):
    """Revoking when api_key_hash is already None must raise HTTPException 400 before any DB access."""
    test_tenant.api_key_hash = None

    with pytest.raises(HTTPException) as exc_info:
        await TenantService.revoke_api_key(session, test_tenant)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No API key to revoke"


async def test_revoke_api_key_invalidates_redis_cache(session, test_tenant):
    """Both tenant:apikey and tenant:id cache keys must be deleted from Redis after revocation."""
    await TenantService.revoke_api_key(session, test_tenant)

    assert redis_client.redis.delete.call_count == 2


async def test_revoked_tenant_invisible_to_api_key_lookup(session, test_tenant):
    """After revocation, querying by the old hash must return None — SQL equality against NULL is UNKNOWN, not TRUE."""
    old_hash = test_tenant.api_key_hash
    await TenantService.revoke_api_key(session, test_tenant)

    result = await session.scalar(
        select(Tenant).where(Tenant.api_key_hash == old_hash)
    )
    assert result is None
