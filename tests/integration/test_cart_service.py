import pytest
from decimal import Decimal
from fastapi import HTTPException
from models.cart_items import CartItem
from services.cart import CartService



def test_get_cart_empty(session, verified_user):
    """Empty cart returns an empty list."""
    cart_items = CartService.get_cart(db=session, user_id=verified_user.id)

    assert cart_items == []


def test_get_cart_returns_items_with_product_loaded(session, verified_user, product_factory):
    """Cart items are returned with the product relationship eagerly loaded."""
    product = product_factory()
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=2)

    cart_items = CartService.get_cart(db=session, user_id=verified_user.id)

    assert len(cart_items) == 1
    assert cart_items[0].product_id == product.id
    assert cart_items[0].quantity == 2
    assert cart_items[0].product is not None
    assert cart_items[0].product.name == "Laptop"




def test_calculate_total_price_empty_cart():
    """Total price of an empty cart is zero."""
    total = CartService.calculate_cart_total_price([])

    assert total == Decimal("0")


def test_calculate_total_price_multiple_items(session, verified_user, product_factory):
    """Total price sums (price * quantity) across all items."""
    p1 = product_factory(name="Laptop", price=1000.00, stock=10)
    p2 = product_factory(name="Mouse", price=50.00, stock=20)
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=p1.id, quantity=2)
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=p2.id, quantity=3)

    cart_items = CartService.get_cart(db=session, user_id=verified_user.id)
    total = CartService.calculate_cart_total_price(cart_items)

    # (1000 * 2) + (50 * 3) = 2150
    assert total == Decimal("2150.00")


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



def test_update_cart_item_success(session, verified_user, product_factory):
    """Updating quantity sets the new value correctly."""
    product = product_factory(stock=10)
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=2)

    cart_item = CartService.update_cart_item(db=session, user_id=verified_user.id, product_id=product.id, new_quantity=5)

    assert cart_item.quantity == 5
    assert cart_item.product is not None


def test_update_cart_item_not_found(session, verified_user, product_factory):
    """Updating a non-existent cart item raises 404."""
    product = product_factory()

    with pytest.raises(HTTPException) as exc:
        CartService.update_cart_item(db=session, user_id=verified_user.id, product_id=product.id, new_quantity=1)

    assert exc.value.status_code == 404


def test_update_cart_item_exceeds_stock(session, verified_user, product_factory):
    """Updating quantity beyond stock raises 409."""
    product = product_factory(stock=5)
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=2)

    with pytest.raises(HTTPException) as exc:
        CartService.update_cart_item(db=session, user_id=verified_user.id, product_id=product.id, new_quantity=6)

    assert exc.value.status_code == 409
    assert exc.value.detail["available_stock"] == 5



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
