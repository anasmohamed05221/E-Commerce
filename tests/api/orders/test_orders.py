import pytest
from models.users import User
from utils.hashing import get_password_hash
from services.cart import CartService
from services.checkout import CheckoutService


async def login(client, verified_user) -> str:
    """Login and return access token."""
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    return response.json()["access_token"]


# ─── Authentication ───────────────────────────────────────────────────────────


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


# ─── GET /orders/ ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_orders_success(client, verified_user, order_factory):
    """Returns 200 with correct envelope shape."""
    token = await login(client, verified_user)
    order_factory()

    response = await client.get("/orders/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "limit" in data
    assert "offset" in data
    assert "total" in data
    assert data["total"] == 1
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_orders_empty(client, verified_user):
    """Returns 200 with empty items list when user has no orders."""
    token = await login(client, verified_user)

    response = await client.get("/orders/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_orders_pagination_params(client, verified_user, order_factory):
    """limit and offset query params are reflected in the response envelope."""
    token = await login(client, verified_user)
    order_factory()
    order_factory()
    order_factory()

    response = await client.get(
        "/orders/?limit=2&offset=1",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert data["total"] == 3
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_orders_invalid_limit(client, verified_user):
    """limit=0 returns 422."""
    token = await login(client, verified_user)

    response = await client.get("/orders/?limit=0", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_orders_invalid_offset(client, verified_user):
    """offset=-1 returns 422."""
    token = await login(client, verified_user)

    response = await client.get("/orders/?offset=-1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422


# ─── GET /orders/{order_id} ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_order_success(client, verified_user, order_factory):
    """Returns 200 with full OrderOut shape including nested items and product."""
    token = await login(client, verified_user)
    order = order_factory()

    response = await client.get(
        f"/orders/{order.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order.id
    assert "total_amount" in data
    assert "status" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert len(data["items"]) > 0
    item = data["items"][0]
    assert "price_at_time" in item
    assert "quantity" in item
    assert "subtotal" in item
    assert "product" in item
    assert "name" in item["product"]


@pytest.mark.asyncio
async def test_get_order_not_found(client, verified_user):
    """Returns 404 for a non-existent order."""
    token = await login(client, verified_user)

    response = await client.get("/orders/99999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_order_other_user(client, verified_user, session, product_factory):
    """Returns 404 when the order belongs to a different user."""
    token = await login(client, verified_user)

    other_user = User(
        email="other@example.com",
        first_name="Other",
        last_name="User",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111112",
        is_verified=True,
        is_active=True
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    product = product_factory()
    CartService.add_to_cart(session, other_user.id, product.id, 1)
    other_order = CheckoutService.checkout(db=session, user_id=other_user.id)

    response = await client.get(
        f"/orders/{other_order.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


# ─── POST /orders/{order_id}/cancel ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_order_success(client, verified_user, order_factory):
    """Returns 200 with status set to cancelled."""
    token = await login(client, verified_user)
    order = order_factory()

    response = await client.post(
        f"/orders/{order.id}/cancel",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_order_not_found(client, verified_user):
    """Returns 404 for a non-existent order."""
    token = await login(client, verified_user)

    response = await client.post("/orders/99999/cancel", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_order_not_pending(client, verified_user, order_factory):
    """Returns 409 when the order is already cancelled."""
    token = await login(client, verified_user)
    order = order_factory()

    await client.post(f"/orders/{order.id}/cancel", headers={"Authorization": f"Bearer {token}"})
    response = await client.post(f"/orders/{order.id}/cancel", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 409