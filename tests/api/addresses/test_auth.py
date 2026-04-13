import pytest


@pytest.mark.asyncio
async def test_create_address_requires_auth(client):
    """POST /addresses/ requires authentication."""
    response = await client.post("/addresses/", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_addresses_requires_auth(client):
    """GET /addresses/ requires authentication."""
    response = await client.get("/addresses/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_address_requires_auth(client):
    """GET /addresses/{id} requires authentication."""
    response = await client.get("/addresses/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_address_requires_auth(client):
    """PATCH /addresses/{id} requires authentication."""
    response = await client.patch("/addresses/1", json={"city": "X"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_address_requires_auth(client):
    """DELETE /addresses/{id} requires authentication."""
    response = await client.delete("/addresses/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_set_default_requires_auth(client):
    """POST /addresses/{id}/set-default requires authentication."""
    response = await client.post("/addresses/1/set-default")
    assert response.status_code == 401
