import pytest
from fastapi import HTTPException
from services.orders import OrderService
from services.cart import CartService
from services.checkout import CheckoutService
from models.users import User
from models.addresses import Address
from models.enums import PaymentMethod
from utils.hashing import get_password_hash


async def test_get_orders_returns_user_orders(session, verified_user, order_factory):
    """Returns all orders belonging to the user with the correct total count."""
    await order_factory()
    await order_factory()
    orders, total = await OrderService.get_orders(session, verified_user.id, 2, 0)

    assert len(orders) == 2
    assert total == 2
    assert all(o.user_id == verified_user.id for o in orders)


async def test_get_orders_empty(session, verified_user):
    """Returns an empty list and zero total when the user has no orders."""
    orders, total = await OrderService.get_orders(session, verified_user.id, 1, 0)

    assert total == 0
    assert orders == []


async def test_get_orders_pagination_offset(session, verified_user, order_factory):
    """Offset skips the correct number of records while total reflects the full count."""
    await order_factory()
    await order_factory()
    await order_factory()

    orders, total = await OrderService.get_orders(session, verified_user.id, 10, 2)

    assert len(orders) == 1
    assert total == 3


async def test_get_order_success(session, verified_user, order_factory):
    """Returns the correct order with items and nested product details eagerly loaded."""
    created_order = await order_factory()

    order = await OrderService.get_order(session, verified_user.id, created_order.id)

    assert order.id == created_order.id
    assert len(order.items) > 0
    assert order.items[0].product is not None


async def test_get_order_not_found(session, verified_user):
    """Raises 404 when the order does not exist."""
    with pytest.raises(HTTPException) as exc:
        await OrderService.get_order(session, verified_user.id, 99)
    assert exc.value.status_code == 404
    assert exc.value.detail == "Order not found"


async def test_get_order_wrong_owner(session, verified_user, product_factory):
    """Raises 404 when the order exists but belongs to a different user."""
    other_user = User(
        email="other@example.com",
        first_name="Other",
        last_name="User",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111112",
        is_verified=True,
        is_active=True
    )
    session.add(other_user)
    await session.commit()
    await session.refresh(other_user)

    addr = Address(user_id=other_user.id, street="1 St", city="Cairo", country="Egypt", postal_code="11511", is_default=True)
    session.add(addr)
    await session.commit()

    product = await product_factory()
    await CartService.add_to_cart(session, other_user.id, product.id, 1)
    other_order = await CheckoutService.checkout(db=session, user_id=other_user.id, address_id=addr.id, payment_method=PaymentMethod.COD)

    with pytest.raises(HTTPException) as exc:
        await OrderService.get_order(session, verified_user.id, other_order.id)
    assert exc.value.status_code == 404
