import pytest
from sqlalchemy import select
from fastapi import HTTPException
from services.products import ProductService
from services.cart import CartService
from services.checkout import CheckoutService
from models.products import Product
from models.cart_items import CartItem
from models.enums import PaymentMethod


async def test_delete_product_success(session, product_factory):
    """Product is removed from the database after deletion."""
    product = await product_factory()
    product_id = product.id

    await ProductService.delete_product(session, product_id)

    assert await session.scalar(select(Product).where(Product.id == product_id)) is None


async def test_delete_product_not_found(session):
    """Raises 404 when product_id does not exist."""
    with pytest.raises(HTTPException) as exc:
        await ProductService.delete_product(session, 99999)

    assert exc.value.status_code == 404


async def test_delete_product_blocked_by_order(session, verified_user, product_factory, test_address):
    """Raises 409 when the product is referenced by an existing order item."""
    product = await product_factory()
    await CartService.add_to_cart(session, verified_user.id, product.id, 1)
    await CheckoutService.checkout(session, verified_user.id, test_address.id, PaymentMethod.COD)

    with pytest.raises(HTTPException) as exc:
        await ProductService.delete_product(session, product.id)

    assert exc.value.status_code == 409


async def test_delete_product_removes_cart_items(session, verified_user, product_factory):
    """Deleting a product that is only in a cart (no orders) succeeds and cascades cart items."""
    product = await product_factory()
    await CartService.add_to_cart(session, verified_user.id, product.id, 2)

    cart_item = await session.scalar(select(CartItem).where(CartItem.product_id == product.id))
    assert cart_item is not None

    await ProductService.delete_product(session, product.id)

    assert await session.scalar(select(CartItem).where(CartItem.product_id == product.id)) is None
    assert await session.scalar(select(Product).where(Product.id == product.id)) is None
