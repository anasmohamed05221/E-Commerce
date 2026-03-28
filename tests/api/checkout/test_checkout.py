import pytest


async def login(client, verified_user) -> str:
    """Login and return access token."""
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    return response.json()["access_token"]


# ─── Authentication ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_checkout_requires_auth(client):
    """Checkout endpoint requires authentication."""
    response = await client.post("/orders/")

    assert response.status_code == 401


# ─── POST /orders/ ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_checkout_success(client, verified_user, product_factory):
    """Successful checkout returns 201 with full order and item details."""
    token = await login(client, verified_user)
    product = product_factory(name="Laptop", price=1000.00, stock=10)

    await client.post("/cart/", json={"product_id": product.id, "quantity": 2},
                      headers={"Authorization": f"Bearer {token}"})

    response = await client.post("/orders/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 201
    data = response.json()
    # Order fields
    assert float(data["total_amount"]) == 2000.00
    assert data["status"] == "pending"
    # Items with product details
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert float(item["price_at_time"]) == 1000.00
    assert item["quantity"] == 2
    assert float(item["subtotal"]) == 2000.00
    assert item["product"]["name"] == "Laptop"


@pytest.mark.asyncio
async def test_checkout_empty_cart(client, verified_user):
    """Checkout with an empty cart returns 400."""
    token = await login(client, verified_user)

    response = await client.post("/orders/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_checkout_insufficient_stock(client, verified_user, session, product_factory):
    """Checkout raises 409 when stock drops below cart quantity before checkout."""
    token = await login(client, verified_user)
    product = product_factory(name="Laptop", price=1000.00, stock=10)

    # Add to cart when stock is sufficient
    await client.post("/cart/", json={"product_id": product.id, "quantity": 5},
                      headers={"Authorization": f"Bearer {token}"})

    # Simulate stock dropping before checkout
    product.stock = 2
    session.commit()

    response = await client.post("/orders/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 409
    assert response.json()["detail"]["message"] == "Not enough stock available"


@pytest.mark.asyncio
async def test_checkout_response_schema(client, verified_user, product_factory):
    """Response includes all expected fields from OrderOut schema."""
    token = await login(client, verified_user)
    product = product_factory(name="Mouse", price=50.00, stock=5)

    await client.post("/cart/", json={"product_id": product.id, "quantity": 1},
                      headers={"Authorization": f"Bearer {token}"})

    response = await client.post("/orders/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 201
    data = response.json()
    # Top-level order fields
    assert "id" in data
    assert "total_amount" in data
    assert "status" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "items" in data
    # Item fields
    item = data["items"][0]
    assert "id" in item
    assert "price_at_time" in item
    assert "quantity" in item
    assert "subtotal" in item
    assert "product" in item
    # Nested product fields
    assert "id" in item["product"]
    assert "name" in item["product"]
    assert "price" in item["product"]


@pytest.mark.asyncio
async def test_checkout_clears_cart(client, verified_user, product_factory):
    """Cart is empty after a successful checkout."""
    token = await login(client, verified_user)
    product = product_factory(name="Keyboard", price=60.00, stock=5)

    await client.post("/cart/", json={"product_id": product.id, "quantity": 1},
                      headers={"Authorization": f"Bearer {token}"})

    await client.post("/orders/", headers={"Authorization": f"Bearer {token}"})

    cart_response = await client.get("/cart/", headers={"Authorization": f"Bearer {token}"})
    assert cart_response.json()["cart_items"] == []
