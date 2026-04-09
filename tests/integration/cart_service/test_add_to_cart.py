import pytest
from fastapi import HTTPException
from models.cart_items import CartItem
from services.cart import CartService


def test_add_to_cart_new_item(session, verified_user, product_factory):
    """Adding a product creates a new cart item with correct quantity."""
    product = product_factory()

    cart_item = CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=3)

    assert cart_item.user_id == verified_user.id
    assert cart_item.product_id == product.id
    assert cart_item.quantity == 3
    assert cart_item.product is not None


def test_add_to_cart_increments_existing_item(session, verified_user, product_factory):
    """Adding the same product again increments quantity instead of duplicating."""
    product = product_factory(stock=10)
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=3)

    cart_item = CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=4)

    assert cart_item.quantity == 7
    # Only one row exists for this user+product
    count = session.query(CartItem).filter_by(user_id=verified_user.id, product_id=product.id).count()
    assert count == 1


def test_add_to_cart_product_not_found(session, verified_user):
    """Adding a non-existent product raises 404."""
    with pytest.raises(HTTPException) as exc:
        CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=9999, quantity=1)

    assert exc.value.status_code == 404


def test_add_to_cart_exceeds_stock_new_item(session, verified_user, product_factory):
    """Adding quantity greater than stock raises 409."""
    product = product_factory(stock=5)

    with pytest.raises(HTTPException) as exc:
        CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=6)

    assert exc.value.status_code == 409
    assert exc.value.detail["available_stock"] == 5


def test_add_to_cart_exceeds_stock_on_increment(session, verified_user, product_factory):
    """Incrementing quantity past stock raises 409."""
    product = product_factory(stock=5)
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=3)

    with pytest.raises(HTTPException) as exc:
        CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=3)

    assert exc.value.status_code == 409
    assert exc.value.detail["available_stock"] == 5
