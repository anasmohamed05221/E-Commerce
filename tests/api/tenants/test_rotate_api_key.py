import hashlib


async def test_rotate_returns_new_api_key(client):
    """Rotation must return 200 with a vnx_-prefixed api_key and a non-empty message."""
    response = await client.post("/tenants/me/rotate-api-key")

    assert response.status_code == 200
    data = response.json()
    assert "api_key" in data
    assert data["api_key"].startswith("vnx_")
    assert "message" in data
    assert data["message"]


async def test_rotate_new_key_stored_in_db(client, session, test_tenant):
    """After rotation, DB api_key_hash must equal SHA256 of the key returned in the response."""
    response = await client.post("/tenants/me/rotate-api-key")

    assert response.status_code == 200
    new_key = response.json()["api_key"]

    await session.refresh(test_tenant)
    expected_hash = hashlib.sha256(new_key.encode()).hexdigest()
    assert test_tenant.api_key_hash == expected_hash


async def test_rotate_response_has_no_sensitive_fields(client):
    """api_key_hash must never appear in the rotation response."""
    response = await client.post("/tenants/me/rotate-api-key")

    assert response.status_code == 200
    assert "api_key_hash" not in response.json()


async def test_rotate_requires_auth(client):
    """Request with an invalid API key must be rejected by the middleware with 401."""
    response = await client.post(
        "/tenants/me/rotate-api-key",
        headers={"X-Tenant-API-Key": "vnx_invalid_key"}
    )
    assert response.status_code == 401
