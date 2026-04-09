import pytest
from services.cart import CartService
from services.checkout import CheckoutService


@pytest.mark.asyncio
async def test_delete_product_success(client, admin_token, product_factory):
    """Admin deletes a product — returns 204 with no body."""
    product = product_factory()

    response = await client.delete(
        f"/admin/products/{product.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 204
    assert response.content == b""


@pytest.mark.asyncio
async def test_delete_product_not_found(client, admin_token):
    """Returns 404 for a non-existent product."""
    response = await client.delete(
        "/admin/products/99999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_product_blocked_by_order(client, admin_token, verified_user, session, product_factory):
    """Returns 409 when the product is referenced by an order item."""
    product = product_factory()
    CartService.add_to_cart(session, verified_user.id, product.id, 1)
    CheckoutService.checkout(session, verified_user.id)

    response = await client.delete(
        f"/admin/products/{product.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_product_with_cart_item_succeeds(client, admin_token, verified_user, session, product_factory):
    """Returns 204 when product is in a cart but has no orders — cart item is cascade-deleted."""
    product = product_factory()
    CartService.add_to_cart(session, verified_user.id, product.id, 2)

    response = await client.delete(
        f"/admin/products/{product.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204
