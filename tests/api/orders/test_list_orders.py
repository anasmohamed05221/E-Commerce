import pytest


@pytest.mark.asyncio
async def test_get_orders_success(client, user_token, order_factory):
    """Returns 200 with correct envelope shape."""
    order_factory()

    response = await client.get("/orders/", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "limit" in data
    assert "offset" in data
    assert "total" in data
    assert data["total"] == 1
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_orders_empty(client, user_token):
    """Returns 200 with empty items list when user has no orders."""
    response = await client.get("/orders/", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_orders_pagination_params(client, user_token, order_factory):
    """limit and offset query params are reflected in the response envelope."""
    order_factory()
    order_factory()
    order_factory()

    response = await client.get(
        "/orders/?limit=2&offset=1",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert data["total"] == 3
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_orders_invalid_limit(client, user_token):
    """limit=0 returns 422."""
    response = await client.get("/orders/?limit=0", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_orders_invalid_offset(client, user_token):
    """offset=-1 returns 422."""
    response = await client.get("/orders/?offset=-1", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 422
