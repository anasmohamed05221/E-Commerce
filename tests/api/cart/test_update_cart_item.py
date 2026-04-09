import pytest


@pytest.mark.asyncio
async def test_update_cart_item_success(client, user_token, session, product_factory):
    """Updating quantity returns 200 with new quantity."""
    product = product_factory(stock=10)

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
async def test_update_cart_item_exceeds_stock(client, user_token, session, product_factory):
    """Updating quantity beyond stock returns 409."""
    product = product_factory(stock=5)

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
