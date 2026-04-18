import pytest
from fastapi import HTTPException
from services.cart import CartService


async def test_update_cart_item_success(session, verified_user, product_factory):
    """Updating quantity sets the new value correctly."""
    product = await product_factory(stock=10)
    await CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=2)

    cart_item = await CartService.update_cart_item(db=session, user_id=verified_user.id, product_id=product.id, new_quantity=5)

    assert cart_item.quantity == 5
    assert cart_item.product is not None


async def test_update_cart_item_not_found(session, verified_user, product_factory):
    """Updating a non-existent cart item raises 404."""
    product = await product_factory()

    with pytest.raises(HTTPException) as exc:
        await CartService.update_cart_item(db=session, user_id=verified_user.id, product_id=product.id, new_quantity=1)

    assert exc.value.status_code == 404


async def test_update_cart_item_exceeds_stock(session, verified_user, product_factory):
    """Updating quantity beyond stock raises 409."""
    product = await product_factory(stock=5)
    await CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=2)

    with pytest.raises(HTTPException) as exc:
        await CartService.update_cart_item(db=session, user_id=verified_user.id, product_id=product.id, new_quantity=6)

    assert exc.value.status_code == 409
    assert exc.value.detail["available_stock"] == 5
