import pytest
from fastapi import HTTPException
from services.orders import OrderService
from models.enums import OrderStatus


def test_update_order_status_pending_to_confirmed(session, verified_user, order_factory):
    """Advances a PENDING order to CONFIRMED and persists the change."""
    order = order_factory()

    updated = OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)

    assert updated.status == OrderStatus.CONFIRMED
    assert len(updated.items) > 0
    assert updated.items[0].product is not None


def test_update_order_status_confirmed_to_completed(session, verified_user, order_factory):
    """Advances a CONFIRMED order to COMPLETED."""
    order = order_factory()
    OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)

    updated = OrderService.update_order_status(session, OrderStatus.COMPLETED, order.id)

    assert updated.status == OrderStatus.COMPLETED


def test_update_order_status_not_found(session):
    """Raises 404 when the order does not exist."""
    with pytest.raises(HTTPException) as exc:
        OrderService.update_order_status(session, OrderStatus.CONFIRMED, 9999)
    assert exc.value.status_code == 404


def test_update_order_status_same_status(session, verified_user, order_factory):
    """Raises 409 when the new status matches the current status."""
    order = order_factory()

    with pytest.raises(HTTPException) as exc:
        OrderService.update_order_status(session, OrderStatus.PENDING, order.id)
    assert exc.value.status_code == 409
    assert "already" in exc.value.detail


def test_update_order_status_skip_confirmed(session, verified_user, order_factory):
    """Raises 409 when trying to skip CONFIRMED (PENDING → COMPLETED)."""
    order = order_factory()

    with pytest.raises(HTTPException) as exc:
        OrderService.update_order_status(session, OrderStatus.COMPLETED, order.id)
    assert exc.value.status_code == 409
    assert "not allowed" in exc.value.detail


def test_update_order_status_from_terminal_cancelled(session, verified_user, order_factory):
    """Raises 409 when trying to advance a CANCELLED order."""
    order = order_factory()
    OrderService.cancel_order(session, verified_user.id, order.id)

    with pytest.raises(HTTPException) as exc:
        OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)
    assert exc.value.status_code == 409


def test_update_order_status_from_terminal_completed(session, verified_user, order_factory):
    """Raises 409 when trying to advance a COMPLETED order."""
    order = order_factory()
    OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)
    OrderService.update_order_status(session, OrderStatus.COMPLETED, order.id)

    with pytest.raises(HTTPException) as exc:
        OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)
    assert exc.value.status_code == 409
