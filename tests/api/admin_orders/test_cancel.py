import pytest
from services.orders import OrderService
from models.enums import OrderStatus


@pytest.mark.asyncio
async def test_admin_cancel_order_success(client, admin_token, session, order_factory):
    """Admin cancels a CONFIRMED order -- returns AdminOrderOut with cancelled status."""
    order = await order_factory()
    await OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)

    response = await client.post(
        f"/admin/orders/{order.id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert "user_id" in data
    assert "items" in data


@pytest.mark.asyncio
async def test_admin_cancel_order_not_found(client, admin_token):
    """Returns 404 for a non-existent order."""
    response = await client.post(
        "/admin/orders/99999/cancel",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_cancel_order_completed(client, admin_token, session, order_factory):
    """Returns 409 when the order is already COMPLETED."""
    order = await order_factory()
    await OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)
    await OrderService.update_order_status(session, OrderStatus.SHIPPED, order.id)
    await OrderService.update_order_status(session, OrderStatus.COMPLETED, order.id)

    response = await client.post(
        f"/admin/orders/{order.id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409