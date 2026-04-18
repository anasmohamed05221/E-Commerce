import pytest


@pytest.mark.asyncio
async def test_get_cart_empty(client, user_token, session):
    """Authenticated user with no items gets an empty cart."""
    response = await client.get("/cart/", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["cart_items"] == []
    assert float(data["total_price"]) == 0


@pytest.mark.asyncio
async def test_get_cart_with_items(client, user_token, session, product_factory):
    """Cart returns items with product details and correct total."""
    p1 = await product_factory(name="Laptop", price=1000.00, stock=10)
    p2 = await product_factory(name="Mouse", price=50.00, stock=20)

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
