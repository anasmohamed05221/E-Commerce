import pytest
from fastapi import HTTPException
from services.orders import OrderService
from services.cart import CartService
from services.checkout import CheckoutService
from models.users import User
from models.addresses import Address
from models.enums import OrderStatus, PaymentMethod
from utils.hashing import get_password_hash


async def test_get_all_orders_empty(session):
    """Returns empty list and zero total when no orders exist."""
    orders, total = await OrderService.get_all_orders(session, limit=10, offset=0)

    assert orders == []
    assert total == 0


async def test_get_all_orders_returns_all_users_orders(session, verified_user, product_factory):
    """Returns orders from all users, not scoped to a single user."""
    other_user = User(
        email="other_admin_test@example.com",
        first_name="Other",
        last_name="User",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201999999999",
        is_verified=True,
        is_active=True
    )
    session.add(other_user)
    await session.commit()
    await session.refresh(other_user)

    # Address for verified_user
    addr1 = Address(user_id=verified_user.id, street="1 St", city="Cairo", country="Egypt", postal_code="11511", is_default=True)
    session.add(addr1)
    # Address for other_user
    addr2 = Address(user_id=other_user.id, street="2 St", city="Cairo", country="Egypt", postal_code="11511", is_default=True)
    session.add(addr2)
    await session.commit()

    # Order for verified_user
    p1 = await product_factory(name="Laptop", stock=10)
    await CartService.add_to_cart(session, verified_user.id, p1.id, 1)
    await CheckoutService.checkout(session, verified_user.id, addr1.id, PaymentMethod.COD)

    # Order for other_user
    p2 = await product_factory(name="Mouse", stock=10)
    await CartService.add_to_cart(session, other_user.id, p2.id, 1)
    await CheckoutService.checkout(session, other_user.id, addr2.id, PaymentMethod.COD)

    orders, total = await OrderService.get_all_orders(session, limit=10, offset=0)

    assert total == 2
    assert len(orders) == 2
    user_ids = {o.user_id for o in orders}
    assert verified_user.id in user_ids
    assert other_user.id in user_ids


async def test_get_all_orders_pagination(session, verified_user, order_factory):
    """Limit and offset control the page; total reflects the full count."""
    await order_factory()
    await order_factory()
    await order_factory()

    orders, total = await OrderService.get_all_orders(session, limit=2, offset=0)

    assert len(orders) == 2
    assert total == 3

    orders_page2, total2 = await OrderService.get_all_orders(session, limit=2, offset=2)

    assert len(orders_page2) == 1
    assert total2 == 3


async def test_get_all_orders_status_filter_match(session, verified_user, order_factory):
    """Filters orders to only the requested status."""
    order = await order_factory()
    await order_factory()  # second order stays PENDING

    await OrderService.cancel_order(session, verified_user.id, order.id)

    orders, total = await OrderService.get_all_orders(session, limit=10, offset=0, status_filter=OrderStatus.CANCELLED)

    assert total == 1
    assert orders[0].status == OrderStatus.CANCELLED


async def test_get_all_orders_status_filter_no_match(session, verified_user, order_factory):
    """Returns empty when no orders match the filter."""
    await order_factory()

    orders, total = await OrderService.get_all_orders(session, limit=10, offset=0, status_filter=OrderStatus.COMPLETED)

    assert total == 0
    assert orders == []


async def test_get_all_orders_newest_first(session, verified_user, order_factory):
    """Orders are returned newest first (descending created_at)."""
    await order_factory()
    await order_factory()

    orders, _ = await OrderService.get_all_orders(session, limit=10, offset=0)

    assert orders[0].created_at >= orders[1].created_at
