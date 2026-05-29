async def test_revoke_returns_message(client):
    """Revocation must return 200 with a non-empty message."""
    response = await client.delete("/tenants/me/api-key")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"]


async def test_revoke_sets_api_key_hash_to_null_in_db(client, session, test_tenant):
    """After revocation, api_key_hash in DB must be None and tenant must remain active."""
    response = await client.delete("/tenants/me/api-key")

    assert response.status_code == 200

    await session.refresh(test_tenant)
    assert test_tenant.api_key_hash is None
    assert test_tenant.is_active is True


async def test_revoke_requires_auth(client):
    """Request with an invalid API key must be rejected by the middleware with 401."""
    response = await client.delete(
        "/tenants/me/api-key",
        headers={"X-Tenant-API-Key": "vnx_invalid_key"}
    )
    assert response.status_code == 401


async def test_revoked_tenant_no_api_key_header_rejected(client):
    """After revocation, a request with no API key header must be rejected — null header must not match null DB hash."""
    revoke_response = await client.delete("/tenants/me/api-key")
    assert revoke_response.status_code == 200

    response = await client.get(
        "/users/me",
        headers={"X-Tenant-API-Key": ""}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Tenant could not be resolved"
