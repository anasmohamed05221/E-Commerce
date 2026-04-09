import pytest
from services.orders import OrderService
from models.enums import OrderStatus


@pytest.mark.asyncio
async def test_get_all_orders_success(client, admin_token, order_factory):
    """Returns 200 with AdminOrderListOut shape — items include user_id."""
    order_factory()

    response = await client.get(
        "/admin/orders/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "limit" in data
    assert "offset" in data
    assert "total" in data
    assert data["total"] == 1
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert "user_id" in item
    assert "status" in item
    assert "total_amount" in item
    assert "created_at" in item


@pytest.mark.asyncio
async def test_get_all_orders_empty(client, admin_token):
    """Returns 200 with empty items when no orders exist."""
    response = await client.get(
        "/admin/orders/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_all_orders_status_filter(client, admin_token, session, order_factory, verified_user):
    """?status=cancelled returns only cancelled orders."""
    order = order_factory()
    order_factory()  # stays PENDING

    OrderService.cancel_order(session, verified_user.id, order.id)

    response = await client.get(
        "/admin/orders/?status=cancelled",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_get_all_orders_pagination(client, admin_token, order_factory):
    """limit and offset control the page; total reflects the full count."""
    order_factory()
    order_factory()
    order_factory()

    response = await client.get(
        "/admin/orders/?limit=2&offset=1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert data["total"] == 3
    assert len(data["items"]) == 2
