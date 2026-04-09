import pytest
import time
from fastapi import HTTPException
from services.orders import OrderService
from services.cart import CartService
from services.checkout import CheckoutService
from models.users import User
from models.enums import OrderStatus
from utils.hashing import get_password_hash


def test_get_all_orders_empty(session):
    """Returns empty list and zero total when no orders exist."""
    orders, total = OrderService.get_all_orders(session, limit=10, offset=0)

    assert orders == []
    assert total == 0


def test_get_all_orders_returns_all_users_orders(session, verified_user, product_factory):
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
    session.commit()
    session.refresh(other_user)

    # Order for verified_user
    p1 = product_factory(name="Laptop", stock=10)
    CartService.add_to_cart(session, verified_user.id, p1.id, 1)
    CheckoutService.checkout(session, verified_user.id)

    # Order for other_user
    p2 = product_factory(name="Mouse", stock=10)
    CartService.add_to_cart(session, other_user.id, p2.id, 1)
    CheckoutService.checkout(session, other_user.id)

    orders, total = OrderService.get_all_orders(session, limit=10, offset=0)

    assert total == 2
    assert len(orders) == 2
    user_ids = {o.user_id for o in orders}
    assert verified_user.id in user_ids
    assert other_user.id in user_ids


def test_get_all_orders_pagination(session, verified_user, order_factory):
    """Limit and offset control the page; total reflects the full count."""
    order_factory()
    order_factory()
    order_factory()

    orders, total = OrderService.get_all_orders(session, limit=2, offset=0)

    assert len(orders) == 2
    assert total == 3

    orders_page2, total2 = OrderService.get_all_orders(session, limit=2, offset=2)

    assert len(orders_page2) == 1
    assert total2 == 3


def test_get_all_orders_status_filter_match(session, verified_user, order_factory):
    """Filters orders to only the requested status."""
    order = order_factory()
    order_factory()  # second order stays PENDING

    OrderService.cancel_order(session, verified_user.id, order.id)

    orders, total = OrderService.get_all_orders(session, limit=10, offset=0, status_filter=OrderStatus.CANCELLED)

    assert total == 1
    assert orders[0].status == OrderStatus.CANCELLED


def test_get_all_orders_status_filter_no_match(session, verified_user, order_factory):
    """Returns empty when no orders match the filter."""
    order_factory()

    orders, total = OrderService.get_all_orders(session, limit=10, offset=0, status_filter=OrderStatus.COMPLETED)

    assert total == 0
    assert orders == []


def test_get_all_orders_newest_first(session, verified_user, order_factory):
    """Orders are returned newest first (descending created_at)."""
    first_order = order_factory()
    second_order = order_factory()

    orders, _ = OrderService.get_all_orders(session, limit=10, offset=0)

    assert orders[0].created_at >= orders[1].created_at
