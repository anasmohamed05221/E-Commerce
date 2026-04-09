import pytest
from fastapi import HTTPException
from services.orders import OrderService
from models.inventory_changes import InventoryChange
from models.enums import OrderStatus, InventoryChangeReason


def test_admin_cancel_pending_order(session, verified_user, order_factory):
    """Admin can cancel a PENDING order — status, stock, and inventory change verified."""
    order = order_factory()
    product = order.items[0].product
    stock_before_cancel = product.stock  # stock after checkout (10 - 2 = 8)

    cancelled = OrderService.admin_cancel_order(session, order.id)

    assert cancelled.status == OrderStatus.CANCELLED
    session.refresh(product)
    assert product.stock == stock_before_cancel + order.items[0].quantity

    inv = session.query(InventoryChange).filter(
        InventoryChange.product_id == product.id,
        InventoryChange.reason == InventoryChangeReason.CANCELLATION
    ).first()
    assert inv is not None
    assert inv.change_amount == order.items[0].quantity


def test_admin_cancel_confirmed_order(session, verified_user, order_factory):
    """Admin can cancel a CONFIRMED order — not limited to PENDING like customers."""
    order = order_factory()
    OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)

    cancelled = OrderService.admin_cancel_order(session, order.id)

    assert cancelled.status == OrderStatus.CANCELLED


def test_admin_cancel_restores_stock_multiple_items(session, verified_user, order_factory, product_factory):
    """Stock is restored for every item in a multi-item order."""
    p1 = product_factory(name="Laptop", stock=10)
    p2 = product_factory(name="Mouse", price=50.00, stock=5)
    order = order_factory([(p1, 2), (p2, 3)])

    OrderService.admin_cancel_order(session, order.id)

    session.refresh(p1)
    session.refresh(p2)
    assert p1.stock == 10
    assert p2.stock == 5


def test_admin_cancel_order_not_found(session):
    """Raises 404 when the order does not exist."""
    with pytest.raises(HTTPException) as exc:
        OrderService.admin_cancel_order(session, 9999)
    assert exc.value.status_code == 404


def test_admin_cancel_completed_order(session, verified_user, order_factory):
    """Raises 409 when trying to cancel a COMPLETED order."""
    order = order_factory()
    OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)
    OrderService.update_order_status(session, OrderStatus.COMPLETED, order.id)

    with pytest.raises(HTTPException) as exc:
        OrderService.admin_cancel_order(session, order.id)
    assert exc.value.status_code == 409


def test_admin_cancel_already_cancelled(session, verified_user, order_factory):
    """Raises 409 when the order is already CANCELLED."""
    order = order_factory()
    OrderService.admin_cancel_order(session, order.id)

    with pytest.raises(HTTPException) as exc:
        OrderService.admin_cancel_order(session, order.id)
    assert exc.value.status_code == 409
