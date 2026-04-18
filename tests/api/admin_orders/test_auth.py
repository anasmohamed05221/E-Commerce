import pytest


# --- Authentication (401) ---


@pytest.mark.asyncio
async def test_get_all_orders_requires_auth(client):
    """GET /admin/orders/ returns 401 without a token."""
    response = await client.get("/admin/orders/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_order_status_requires_auth(client):
    """PATCH /admin/orders/{id}/status returns 401 without a token."""
    response = await client.patch("/admin/orders/1/status", json={"status": "confirmed"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cancel_order_requires_auth(client):
    """POST /admin/orders/{id}/cancel returns 401 without a token."""
    response = await client.post("/admin/orders/1/cancel")
    assert response.status_code == 401


# --- Authorization (403) ---


@pytest.mark.asyncio
async def test_get_all_orders_forbidden_for_customer(client, user_token):
    """Customer role is rejected with 403."""
    response = await client.get(
        "/admin/orders/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_order_status_forbidden_for_customer(client, user_token, order_factory):
    """Customer role is rejected with 403."""
    order = await order_factory()
    response = await client.patch(
        f"/admin/orders/{order.id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cancel_order_forbidden_for_customer(client, user_token, order_factory):
    """Customer role is rejected with 403."""
    order = await order_factory()
    response = await client.post(
        f"/admin/orders/{order.id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403