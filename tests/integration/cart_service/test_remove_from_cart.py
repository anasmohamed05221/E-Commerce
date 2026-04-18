import pytest
from sqlalchemy import select, func
from fastapi import HTTPException
from models.cart_items import CartItem
from services.cart import CartService


async def test_remove_from_cart_success(session, verified_user, product_factory):
    """Removing an item deletes it from the database."""
    product = await product_factory()
    await CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=1)

    await CartService.remove_from_cart(db=session, user_id=verified_user.id, product_id=product.id)

    remaining = await session.scalar(
        select(func.count()).select_from(CartItem).where(CartItem.user_id == verified_user.id)
    )
    assert remaining == 0


async def test_remove_from_cart_not_found(session, verified_user):
    """Removing a non-existent cart item raises 404."""
    with pytest.raises(HTTPException) as exc:
        await CartService.remove_from_cart(db=session, user_id=verified_user.id, product_id=9999)

    assert exc.value.status_code == 404
