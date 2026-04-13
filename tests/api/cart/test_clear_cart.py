import pytest


@pytest.mark.asyncio
async def test_clear_cart_success(client, user_token, product_factory):
    """DELETE /cart returns 204 and the cart is empty afterwards."""
    product = product_factory()
    await client.post(
        "/cart/",
        json={"product_id": product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    response = await client.delete("/cart/", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 204
    assert response.content == b""

    cart = await client.get("/cart/", headers={"Authorization": f"Bearer {user_token}"})
    assert cart.json()["cart_items"] == []


@pytest.mark.asyncio
async def test_clear_cart_idempotent_empty_cart(client, user_token):
    """DELETE /cart returns 204 even when the cart is already empty."""
    response = await client.delete("/cart/", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 204
