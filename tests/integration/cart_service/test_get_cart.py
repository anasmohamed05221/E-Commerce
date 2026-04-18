import pytest
from decimal import Decimal
from services.cart import CartService


async def test_get_cart_empty(session, verified_user):
    """Empty cart returns an empty list."""
    cart_items = await CartService.get_cart(db=session, user_id=verified_user.id)

    assert cart_items == []


async def test_get_cart_returns_items_with_product_loaded(session, verified_user, product_factory):
    """Cart items are returned with the product relationship eagerly loaded."""
    product = await product_factory()
    await CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=2)

    cart_items = await CartService.get_cart(db=session, user_id=verified_user.id)

    assert len(cart_items) == 1
    assert cart_items[0].product_id == product.id
    assert cart_items[0].quantity == 2
    assert cart_items[0].product is not None
    assert cart_items[0].product.name == "Laptop"


def test_calculate_total_price_empty_cart():
    """Total price of an empty cart is zero."""
    total = CartService.calculate_cart_total_price([])

    assert total == Decimal("0")


async def test_calculate_total_price_multiple_items(session, verified_user, product_factory):
    """Total price sums (price * quantity) across all items."""
    p1 = await product_factory(name="Laptop", price=1000.00, stock=10)
    p2 = await product_factory(name="Mouse", price=50.00, stock=20)
    await CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=p1.id, quantity=2)
    await CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=p2.id, quantity=3)

    cart_items = await CartService.get_cart(db=session, user_id=verified_user.id)
    total = CartService.calculate_cart_total_price(cart_items)

    # (1000 * 2) + (50 * 3) = 2150
    assert total == Decimal("2150.00")
