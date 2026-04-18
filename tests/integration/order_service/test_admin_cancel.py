import pytest
from sqlalchemy import select
from fastapi import HTTPException
from services.orders import OrderService
from models.inventory_changes import InventoryChange
from models.enums import OrderStatus, InventoryChangeReason


async def test_admin_cancel_pending_order(session, verified_user, order_factory):
    """Admin can cancel a PENDING order -- status, stock, and inventory change verified."""
    order = await order_factory()
    product = order.items[0].product
    stock_before_cancel = product.stock  # stock after checkout (10 - 2 = 8)

    cancelled = await OrderService.admin_cancel_order(session, order.id)

    assert cancelled.status == OrderStatus.CANCELLED
    await session.refresh(product)
    assert product.stock == stock_before_cancel + order.items[0].quantity

    inv = await session.scalar(
        select(InventoryChange).where(
            InventoryChange.product_id == product.id,
            InventoryChange.reason == InventoryChangeReason.CANCELLATION
        )
    )
    assert inv is not None
    assert inv.change_amount == order.items[0].quantity


async def test_admin_cancel_confirmed_order(session, verified_user, order_factory):
    """Admin can cancel a CONFIRMED order -- not limited to PENDING like customers."""
    order = await order_factory()
    await OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)

    cancelled = await OrderService.admin_cancel_order(session, order.id)

    assert cancelled.status == OrderStatus.CANCELLED


async def test_admin_cancel_restores_stock_multiple_items(session, verified_user, order_factory, product_factory):
    """Stock is restored for every item in a multi-item order."""
    p1 = await product_factory(name="Laptop", stock=10)
    p2 = await product_factory(name="Mouse", price=50.00, stock=5)
    order = await order_factory([(p1, 2), (p2, 3)])

    await OrderService.admin_cancel_order(session, order.id)

    await session.refresh(p1)
    await session.refresh(p2)
    assert p1.stock == 10
    assert p2.stock == 5


async def test_admin_cancel_order_not_found(session):
    """Raises 404 when the order does not exist."""
    with pytest.raises(HTTPException) as exc:
        await OrderService.admin_cancel_order(session, 9999)
    assert exc.value.status_code == 404


async def test_admin_cancel_completed_order(session, verified_user, order_factory):
    """Raises 409 when trying to cancel a COMPLETED order."""
    order = await order_factory()
    await OrderService.update_order_status(session, OrderStatus.CONFIRMED, order.id)
    await OrderService.update_order_status(session, OrderStatus.SHIPPED, order.id)
    await OrderService.update_order_status(session, OrderStatus.COMPLETED, order.id)

    with pytest.raises(HTTPException) as exc:
        await OrderService.admin_cancel_order(session, order.id)
    assert exc.value.status_code == 409


async def test_admin_cancel_already_cancelled(session, verified_user, order_factory):
    """Raises 409 when the order is already CANCELLED."""
    order = await order_factory()
    await OrderService.admin_cancel_order(session, order.id)

    with pytest.raises(HTTPException) as exc:
        await OrderService.admin_cancel_order(session, order.id)
    assert exc.value.status_code == 409
