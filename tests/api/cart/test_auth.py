import pytest


@pytest.mark.asyncio
async def test_get_cart_requires_auth(client):
    """All cart endpoints require authentication."""
    response = await client.get("/cart/")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_add_to_cart_requires_auth(client):
    response = await client.post("/cart/", json={"product_id": 1, "quantity": 1})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_cart_requires_auth(client):
    response = await client.patch("/cart/1", json={"quantity": 2})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_cart_requires_auth(client):
    response = await client.delete("/cart/1")

    assert response.status_code == 401
