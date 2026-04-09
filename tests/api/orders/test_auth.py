import pytest


@pytest.mark.asyncio
async def test_get_orders_requires_auth(client):
    """GET /orders/ returns 401 without a token."""
    response = await client.get("/orders/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_order_requires_auth(client):
    """GET /orders/{id} returns 401 without a token."""
    response = await client.get("/orders/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cancel_order_requires_auth(client):
    """POST /orders/{id}/cancel returns 401 without a token."""
    response = await client.post("/orders/1/cancel")
    assert response.status_code == 401
