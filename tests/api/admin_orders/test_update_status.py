import pytest


@pytest.mark.asyncio
async def test_update_order_status_success(client, admin_token, order_factory):
    """Advances PENDING -> CONFIRMED -- returns AdminOrderOut with user_id."""
    order = await order_factory()

    response = await client.patch(
        f"/admin/orders/{order.id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert "user_id" in data
    assert "items" in data
    assert len(data["items"]) > 0
    assert "product" in data["items"][0]


@pytest.mark.asyncio
async def test_update_order_status_not_found(client, admin_token):
    """Returns 404 for a non-existent order."""
    response = await client.patch(
        "/admin/orders/99999/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_order_status_invalid_transition(client, admin_token, order_factory):
    """Returns 409 when trying to skip CONFIRMED (PENDING -> COMPLETED)."""
    order = await order_factory()

    response = await client.patch(
        f"/admin/orders/{order.id}/status",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_order_status_invalid_body(client, admin_token):
    """Returns 422 when the status value is not a valid OrderStatus."""
    response = await client.patch(
        "/admin/orders/1/status",
        json={"status": "wrongStatus"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422