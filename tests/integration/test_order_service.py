import pytest
from fastapi import HTTPException
from services.orders import OrderService
from services.cart import CartService
from services.checkout import CheckoutService
from models.users import User
from models.inventory_changes import InventoryChange
from models.enums import OrderStatus
from utils.hashing import get_password_hash
import time

def test_get_orders_returns_user_orders(session, verified_user, order_factory):
    """Returns all orders belonging to the user with the correct total count."""
    order_factory()
    order_factory()
    orders, total = OrderService.get_orders(session, verified_user.id, 2, 0)

    assert len(orders) == 2
    assert total == 2
    assert all(o.user_id == verified_user.id for o in orders)


def test_get_orders_empty(session, verified_user):
    """Returns an empty list and zero total when the user has no orders."""
    orders, total = OrderService.get_orders(session, verified_user.id, 1, 0)

    assert total == 0
    assert orders == []


def test_get_orders_pagination_offset(session, verified_user, order_factory):
    """Offset skips the correct number of records while total reflects the full count."""
    order_factory()
    order_factory()
    order_factory()
    
    orders, total = OrderService.get_orders(session, verified_user.id, 10, 2)

    assert len(orders)==1
    assert total == 3


def test_get_orders_sorted_newest_first(session, verified_user, order_factory):
    """Most recently created order appears first in the result list."""
    order_factory()
    time.sleep(0.3)
    order_factory()

    orders, total = OrderService.get_orders(session, verified_user.id, 2, 0)

    assert orders[0].created_at > orders[1].created_at


def test_get_order_success(session, verified_user, order_factory):
    """Returns the correct order with items and nested product details eagerly loaded."""
    created_order = order_factory()

    order = OrderService.get_order(session, verified_user.id, created_order.id)

    assert order.id == created_order.id
    assert len(order.items) > 0
    assert order.items[0].product is not None


def test_get_order_not_found(session, verified_user):
    """Raises 404 when the order does not exist."""
    with pytest.raises(HTTPException) as exc:
        order = OrderService.get_order(session, verified_user.id, 99)
    assert exc.value.status_code == 404
    assert exc.value.detail == "Order not found"


def test_get_order_wrong_owner(session, verified_user, product_factory):
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
    session.commit()
    session.refresh(other_user)

    product = product_factory()
    CartService.add_to_cart(session, other_user.id, product.id, 1)
    other_order = CheckoutService.checkout(db=session, user_id=other_user.id)

    with pytest.raises(HTTPException) as exc:
        OrderService.get_order(session, verified_user.id, other_order.id)
    assert exc.value.status_code == 404


def test_cancel_order_success(session, verified_user, order_factory):
    """Cancellation sets status to CANCELLED, restores stock, and logs an inventory change."""
    created_order = order_factory()
    
    cancelled_order = OrderService.cancel_order(session, verified_user.id, created_order.id)
    assert cancelled_order.status == OrderStatus.CANCELLED

    product = cancelled_order.items[0].product
    session.refresh(product)
    assert product.stock == 10

    inv_change = session.query(InventoryChange).filter(
        InventoryChange.product_id == product.id
    ).order_by(InventoryChange.id.desc()).first()
    assert inv_change.change_amount == 2
    assert inv_change.reason.value == "cancellation"


def test_cancel_order_multiple_items(session, verified_user, order_factory, product_factory):
    """Stock is restored and inventory changes are logged for every item in the order, not just the first."""
    p1 = product_factory(name="Laptop", stock=10)
    p2 = product_factory(name="Mouse", price=50.00, stock=5)
    order = order_factory([(p1, 2), (p2, 3)])

    OrderService.cancel_order(session, verified_user.id, order.id)

    session.refresh(p1)
    session.refresh(p2)
    assert p1.stock == 10
    assert p2.stock == 5

    inv_p1 = session.query(InventoryChange).filter(
        InventoryChange.product_id == p1.id
    ).order_by(InventoryChange.id.desc()).first()
    inv_p2 = session.query(InventoryChange).filter(
        InventoryChange.product_id == p2.id
    ).order_by(InventoryChange.id.desc()).first()
    assert inv_p1.change_amount == 2
    assert inv_p1.reason.value == "cancellation"
    assert inv_p2.change_amount == 3
    assert inv_p2.reason.value == "cancellation"


def test_cancel_order_not_found(session, verified_user):
    """Raises 404 when the order does not exist."""
    with pytest.raises(HTTPException) as exc:
        OrderService.cancel_order(session, verified_user.id, 99)
    assert exc.value.status_code == 404


def test_cancel_order_wrong_owner(session, verified_user, product_factory):
    """Raises 404 when the order exists but belongs to a different user."""
    other_user = User(
        email="other2@example.com",
        first_name="Other",
        last_name="User",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111113",
        is_verified=True,
        is_active=True
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    product = product_factory()
    CartService.add_to_cart(session, other_user.id, product.id, 1)
    other_order = CheckoutService.checkout(db=session, user_id=other_user.id)

    with pytest.raises(HTTPException) as exc:
        OrderService.cancel_order(session, verified_user.id, other_order.id)
    assert exc.value.status_code == 404


def test_cancel_order_already_cancelled(session, verified_user, order_factory):
    """Raises 409 when attempting to cancel an order that is already cancelled."""
    order = order_factory()
    OrderService.cancel_order(session, verified_user.id, order.id)

    with pytest.raises(HTTPException) as exc:
        OrderService.cancel_order(session, verified_user.id, order.id)
    assert exc.value.status_code == 409
