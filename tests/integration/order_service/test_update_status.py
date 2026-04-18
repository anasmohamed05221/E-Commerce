import pytest
from fastapi import HTTPException
from services.orders import OrderService
from models.enums import OrderStatus


async def test_update_order_status_pending_to_confirmed(session, verified_user, order_factory):
    """Advances a PENDING order to CONFIRMED and persists the change."""
    order = await order_factory()

    updated = await OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)

    assert updated.status == OrderStatus.CONFIRMED
    assert len(updated.items) > 0
    assert updated.items[0].product is not None


async def test_update_order_status_confirmed_to_completed(session, verified_user, order_factory):
    """Advances an order through the full happy path to COMPLETED."""
    order = await order_factory()
    await OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)
    await OrderService.update_order_status(session, OrderStatus.SHIPPED, order.id)

    updated = await OrderService.update_order_status(session, OrderStatus.COMPLETED, order.id)

    assert updated.status == OrderStatus.COMPLETED


async def test_update_order_status_not_found(session):
    """Raises 404 when the order does not exist."""
    with pytest.raises(HTTPException) as exc:
        await OrderService.update_order_status(session, OrderStatus.CONFIRMED, 9999)
    assert exc.value.status_code == 404


async def test_update_order_status_same_status(session, verified_user, order_factory):
    """Raises 409 when the new status matches the current status."""
    order = await order_factory()

    with pytest.raises(HTTPException) as exc:
        await OrderService.update_order_status(session, OrderStatus.PENDING, order.id)
    assert exc.value.status_code == 409
    assert "already" in exc.value.detail


async def test_update_order_status_skip_confirmed(session, verified_user, order_factory):
    """Raises 409 when trying to skip CONFIRMED (PENDING -> COMPLETED)."""
    order = await order_factory()

    with pytest.raises(HTTPException) as exc:
        await OrderService.update_order_status(session, OrderStatus.COMPLETED, order.id)
    assert exc.value.status_code == 409
    assert "not allowed" in exc.value.detail


async def test_update_order_status_from_terminal_cancelled(session, verified_user, order_factory):
    """Raises 409 when trying to advance a CANCELLED order."""
    order = await order_factory()
    await OrderService.cancel_order(session, verified_user.id, order.id)

    with pytest.raises(HTTPException) as exc:
        await OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)
    assert exc.value.status_code == 409


async def test_update_order_status_from_terminal_completed(session, verified_user, order_factory):
    """Raises 409 when trying to advance a COMPLETED order."""
    order = await order_factory()
    await OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)
    await OrderService.update_order_status(session, OrderStatus.SHIPPED, order.id)
    await OrderService.update_order_status(session, OrderStatus.COMPLETED, order.id)

    with pytest.raises(HTTPException) as exc:
        await OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)
    assert exc.value.status_code == 409
