import pytest
from fastapi import HTTPException
from services.products import ProductService
from services.cart import CartService
from services.checkout import CheckoutService
from models.products import Product
from models.cart_items import CartItem


def test_delete_product_success(session, product_factory):
    """Product is removed from the database after deletion."""
    product = product_factory()
    product_id = product.id

    ProductService.delete_product(session, product_id)

    assert session.query(Product).filter(Product.id == product_id).first() is None


def test_delete_product_not_found(session):
    """Raises 404 when product_id does not exist."""
    with pytest.raises(HTTPException) as exc:
        ProductService.delete_product(session, 99999)

    assert exc.value.status_code == 404


def test_delete_product_blocked_by_order(session, verified_user, product_factory):
    """Raises 409 when the product is referenced by an existing order item."""
    product = product_factory()
    CartService.add_to_cart(session, verified_user.id, product.id, 1)
    CheckoutService.checkout(session, verified_user.id)

    with pytest.raises(HTTPException) as exc:
        ProductService.delete_product(session, product.id)

    assert exc.value.status_code == 409


def test_delete_product_removes_cart_items(session, verified_user, product_factory):
    """Deleting a product that is only in a cart (no orders) succeeds and cascades cart items."""
    product = product_factory()
    CartService.add_to_cart(session, verified_user.id, product.id, 2)

    cart_item = session.query(CartItem).filter(CartItem.product_id == product.id).first()
    assert cart_item is not None

    ProductService.delete_product(session, product.id)

    assert session.query(CartItem).filter(CartItem.product_id == product.id).first() is None
    assert session.query(Product).filter(Product.id == product.id).first() is None
