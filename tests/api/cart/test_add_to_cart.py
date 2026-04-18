import pytest


@pytest.mark.asyncio
async def test_add_to_cart_success(client, user_token, session, product_factory):
    """Adding a valid product returns 201 with cart item details."""
    product = await product_factory()

    response = await client.post("/cart/", json={"product_id": product.id, "quantity": 3},
                                 headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 3
    assert data["product"]["name"] == "Laptop"


@pytest.mark.asyncio
async def test_add_to_cart_increments_existing(client, user_token, session, product_factory):
    """Adding the same product twice increments quantity."""
    product = await product_factory(stock=10)

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
async def test_add_to_cart_exceeds_stock(client, user_token, session, product_factory):
    """Adding quantity beyond stock returns 409."""
    product = await product_factory(stock=5)

    response = await client.post("/cart/", json={"product_id": product.id, "quantity": 6},
                                 headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 409
    assert response.json()["detail"]["available_stock"] == 5


@pytest.mark.asyncio
async def test_add_to_cart_invalid_quantity(client, user_token, session, product_factory):
    """Quantity below 1 or above 100 is rejected by Pydantic validation."""
    product = await product_factory()

    response = await client.post("/cart/", json={"product_id": product.id, "quantity": 0},
                                 headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 422
