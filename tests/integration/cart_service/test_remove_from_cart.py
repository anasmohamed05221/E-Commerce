import pytest
from fastapi import HTTPException
from models.cart_items import CartItem
from services.cart import CartService


def test_remove_from_cart_success(session, verified_user, product_factory):
    """Removing an item deletes it from the database."""
    product = product_factory()
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=1)

    CartService.remove_from_cart(db=session, user_id=verified_user.id, product_id=product.id)

    remaining = session.query(CartItem).filter_by(user_id=verified_user.id).count()
    assert remaining == 0


def test_remove_from_cart_not_found(session, verified_user):
    """Removing a non-existent cart item raises 404."""
    with pytest.raises(HTTPException) as exc:
        CartService.remove_from_cart(db=session, user_id=verified_user.id, product_id=9999)

    assert exc.value.status_code == 404
