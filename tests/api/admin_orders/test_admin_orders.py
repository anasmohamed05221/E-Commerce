import pytest
from services.orders import OrderService
from models.enums import OrderStatus


# ─── Authentication ───────────────────────────────────────────────────────────


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


# ─── Authorization ────────────────────────────────────────────────────────────


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
    order = order_factory()
    response = await client.patch(
        f"/admin/orders/{order.id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cancel_order_forbidden_for_customer(client, user_token, order_factory):
    """Customer role is rejected with 403."""
    order = order_factory()
    response = await client.post(
        f"/admin/orders/{order.id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


# ─── GET /admin/orders/ ──────────────────────────────────────────────────────


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


# ─── PATCH /admin/orders/{id}/status ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_order_status_success(client, admin_token, order_factory):
    """Advances PENDING → CONFIRMED — returns AdminOrderOut with user_id."""
    order = order_factory()

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
    """Returns 409 when trying to skip CONFIRMED (PENDING → COMPLETED)."""
    order = order_factory()

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


# ─── POST /admin/orders/{id}/cancel ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_cancel_order_success(client, admin_token, session, order_factory):
    """Admin cancels a CONFIRMED order — returns AdminOrderOut with cancelled status."""
    order = order_factory()
    OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)

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
    order = order_factory()
    OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)
    OrderService.update_order_status(session, OrderStatus.COMPLETED, order.id)

    response = await client.post(
        f"/admin/orders/{order.id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409
