import pytest


@pytest.mark.asyncio
async def test_remove_from_cart_success(client, user_token, session, product_factory):
    """Removing an item returns 204 and the cart no longer contains it."""
    product = await product_factory()

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
