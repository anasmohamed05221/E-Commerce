import pytest
from models.categories import Category
from models.products import Product


def seed_product(session, *, name="Laptop", price=1000.00, stock=10) -> Product:
    """Create a product with a category for cart tests."""
    category = session.query(Category).first()
    if not category:
        category = Category(name="Electronics", description="Tech gear")
        session.add(category)
        session.commit()
        session.refresh(category)

    product = Product(name=name, price=price, stock=stock, category_id=category.id)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


# ─── Authentication ──────────────────────────────────────────────────────────


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


# ─── GET /cart/ ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_cart_empty(client, user_token, session):
    """Authenticated user with no items gets an empty cart."""
    response = await client.get("/cart/", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["cart_items"] == []
    assert float(data["total_price"]) == 0


@pytest.mark.asyncio
async def test_get_cart_with_items(client, user_token, session):
    """Cart returns items with product details and correct total."""
    p1 = seed_product(session, name="Laptop", price=1000.00, stock=10)
    p2 = seed_product(session, name="Mouse", price=50.00, stock=20)

    # Add two different products
    await client.post("/cart/", json={"product_id": p1.id, "quantity": 2},
                      headers={"Authorization": f"Bearer {user_token}"})
    await client.post("/cart/", json={"product_id": p2.id, "quantity": 3},
                      headers={"Authorization": f"Bearer {user_token}"})

    response = await client.get("/cart/", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 200
    data = response.json()
    assert len(data["cart_items"]) == 2
    # (1000 * 2) + (50 * 3) = 2150
    assert float(data["total_price"]) == 2150.00

    # Verify nested product data is serialized
    item = data["cart_items"][0]
    assert "product" in item
    assert "name" in item["product"]
    assert "price" in item["product"]


# ─── POST /cart/ ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_to_cart_success(client, user_token, session):
    """Adding a valid product returns 201 with cart item details."""
    product = seed_product(session)

    response = await client.post("/cart/", json={"product_id": product.id, "quantity": 3},
                                 headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 3
    assert data["product"]["name"] == "Laptop"


@pytest.mark.asyncio
async def test_add_to_cart_increments_existing(client, user_token, session):
    """Adding the same product twice increments quantity."""
    product = seed_product(session, stock=10)

    await client.post("/cart/", json={"product_id": product.id, "quantity": 3},
                      headers={"Authorization": f"Bearer {user_token}"})
    response = await client.post("/cart/", json={"product_id": product.id, "quantity": 4},
                                 headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 201
    assert response.json()["quantity"] == 7


@pytest.mark.asyncio
async def test_add_to_cart_product_not_found(client, user_token, session):
    """Adding a non-existent product returns 404."""
    response = await client.post("/cart/", json={"product_id": 9999, "quantity": 1},
                                 headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_to_cart_exceeds_stock(client, user_token, session):
    """Adding quantity beyond stock returns 409."""
    product = seed_product(session, stock=5)

    response = await client.post("/cart/", json={"product_id": product.id, "quantity": 6},
                                 headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 409
    assert response.json()["detail"]["available_stock"] == 5


@pytest.mark.asyncio
async def test_add_to_cart_invalid_quantity(client, user_token, session):
    """Quantity below 1 or above 100 is rejected by Pydantic validation."""
    product = seed_product(session)

    response = await client.post("/cart/", json={"product_id": product.id, "quantity": 0},
                                 headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 422


# ─── PATCH /cart/{product_id} ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_cart_item_success(client, user_token, session):
    """Updating quantity returns 200 with new quantity."""
    product = seed_product(session, stock=10)

    await client.post("/cart/", json={"product_id": product.id, "quantity": 2},
                      headers={"Authorization": f"Bearer {user_token}"})

    response = await client.patch(f"/cart/{product.id}", json={"quantity": 5},
                                  headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 200
    assert response.json()["quantity"] == 5


@pytest.mark.asyncio
async def test_update_cart_item_not_found(client, user_token, session):
    """Updating an item not in the cart returns 404."""
    response = await client.patch("/cart/9999", json={"quantity": 1},
                                  headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_cart_item_exceeds_stock(client, user_token, session):
    """Updating quantity beyond stock returns 409."""
    product = seed_product(session, stock=5)

    await client.post("/cart/", json={"product_id": product.id, "quantity": 2},
                      headers={"Authorization": f"Bearer {user_token}"})

    response = await client.patch(f"/cart/{product.id}", json={"quantity": 6},
                                  headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 409
    assert response.json()["detail"]["available_stock"] == 5


@pytest.mark.asyncio
async def test_update_cart_item_invalid_quantity(client, user_token):
    """Quantity below 1 is rejected by Pydantic validation."""
    response = await client.patch("/cart/1", json={"quantity": 0},
                                  headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 422


# ─── DELETE /cart/{product_id} ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_remove_from_cart_success(client, user_token, session):
    """Removing an item returns 204 and the cart no longer contains it."""
    product = seed_product(session)

    await client.post("/cart/", json={"product_id": product.id, "quantity": 1},
                      headers={"Authorization": f"Bearer {user_token}"})

    response = await client.delete(f"/cart/{product.id}",
                                   headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 204

    # Verify item is gone
    cart_response = await client.get("/cart/", headers={"Authorization": f"Bearer {user_token}"})
    assert cart_response.json()["cart_items"] == []


@pytest.mark.asyncio
async def test_remove_from_cart_not_found(client, user_token):
    """Removing an item not in the cart returns 404."""
    response = await client.delete("/cart/9999",
                                   headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 404
