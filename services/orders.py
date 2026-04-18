from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload, selectinload
from models.orders import Order
from models.order_items import OrderItem
from models.enums import OrderStatus, InventoryChangeReason
from models.inventory_changes import InventoryChange
from models.products import Product
from utils.logger import get_logger
from typing import Optional


logger = get_logger(__name__)

class OrderService:

    @staticmethod
    async def get_orders(db: AsyncSession, user_id: int, limit: int, offset: int) -> tuple[list[Order], int]:
        """Return a paginated list of the user's orders and the total count.

        Orders are returned newest first. Total reflects all matching orders
        before pagination, used by the caller to build the response envelope.
        """
        query = select(Order).where(Order.user_id==user_id).order_by(Order.created_at.desc())
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        orders = (await db.scalars(query.offset(offset).limit(limit))).all()

        return orders, total


    @staticmethod
    async def get_order(db: AsyncSession, user_id: int, order_id: int) -> Order:
        """Return a single order with its items and products, enforcing ownership.

        Raises:
            HTTPException 404: If the order does not exist or belongs to another user.
        """
        order = await db.scalar(select(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).where(
            Order.user_id==user_id, Order.id==order_id
        ))

        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        return order


    @staticmethod
    async def _restore_stock_for_order(db: AsyncSession, order: Order) -> None:
        """Restore stock for every item in the order and log inventory changes.
        
        Locks product rows in deterministic order (sorted by product_id) to
        prevent deadlocks. Does not commit — caller owns the transaction.
        """
        sorted_items = sorted(order.items, key=lambda item: item.product_id)
        for item in sorted_items:
            product = await db.scalar(select(Product).where(Product.id==item.product_id).with_for_update())
            product.stock += item.quantity
            inventory_change = InventoryChange(product_id=product.id, change_amount=item.quantity, reason=InventoryChangeReason.CANCELLATION)
            db.add(inventory_change)


    @staticmethod
    async def cancel_order(db: AsyncSession, user_id: int, order_id: int):
        """Cancel a customer's pending order atomically — restore stock and log inventory.

        Policy: customers can only cancel PENDING orders. CONFIRMED+ requires admin.

        Raises 404 (not found / wrong owner), 409 (not pending), 500 (commit failure).
        """
        order = await db.scalar(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id==user_id, Order.id==order_id)
            .with_for_update()
        )

        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending orders can be cancelled")
        
        await OrderService._restore_stock_for_order(db, order)
        order.status = OrderStatus.CANCELLED

        try:
           await db.commit()
        except Exception:
            logger.error("Order cancellation commit failed", extra={"user_id": user_id, "order_id": order_id}, exc_info=True)
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Order cancellation failed")

        order_eagered = await db.scalar(select(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).where(
            Order.user_id==user_id, Order.id==order.id))
        return order_eagered
    

    @staticmethod
    async def get_all_orders(db: AsyncSession, limit: int, offset: int, status_filter: Optional[OrderStatus]=None) -> tuple[list[Order], int]:
        """Return a paginated list of all orders across all users for admin view.

        Optionally filters by order status. Orders are returned newest first.
        Total reflects all matching orders before pagination.
        """
        query = select(Order).order_by(Order.created_at.desc())
        if status_filter is not None:
            query = query.where(Order.status == status_filter)
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        orders = (await db.scalars(query.offset(offset).limit(limit))).all()

        return orders, total
    

    @staticmethod
    def _is_allowed_status_transition(current_status: OrderStatus, new_status: OrderStatus):
        """Check whether a status transition is permitted by the order FSM.

        Terminal states (COMPLETED, CANCELLED) have no valid transitions.
        Returns False for same-status checks — caller handles that separately.
        """
        allowed_transitions = {
            OrderStatus.PENDING: OrderStatus.CONFIRMED,
            OrderStatus.CONFIRMED: OrderStatus.SHIPPED,
            OrderStatus.SHIPPED: OrderStatus.COMPLETED
        }

        if current_status not in allowed_transitions.keys():
            return False
        return new_status == allowed_transitions[current_status]
    
    
    @staticmethod
    async def update_order_status(db: AsyncSession, new_status: OrderStatus, order_id: int):
        """Advance an order through its lifecycle (PENDING→CONFIRMED→SHIPPED→COMPLETED).

        Locks the order row before validation to prevent TOCTOU races.
        Cancellation is not handled here — use cancel_order / admin_cancel_order.

        Raises 404 (not found), 409 (invalid/unchanged transition), 500 (commit failure).
        """
        order = await db.scalar(select(Order).where(Order.id==order_id).with_for_update())

        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        if order.status == new_status:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Order status is already '{new_status.value}'")
        
        if not OrderService._is_allowed_status_transition(order.status, new_status):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Transition from '{order.status.value}' to '{new_status.value}' is not allowed"
            )

        order.status = new_status
        try:
           await db.commit()
        except Exception:
            logger.error("Order status update commit failed", extra={"order_id": order_id}, exc_info=True)
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Order status update failed")

        order_eagered = await db.scalar(select(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).where(
            Order.id==order.id))
        return order_eagered


    @staticmethod
    async def admin_cancel_order(db: AsyncSession, order_id: int) -> Order:
        """Cancel any non-terminal order atomically — restore stock and log inventory.

        Policy: admin can cancel PENDING and CONFIRMED orders (unlike customers, who
        can only cancel PENDING). No ownership check.

        Raises 404 (not found), 409 (already completed/cancelled), 500 (commit failure).
        """
        order = await db.scalar(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id==order_id)
            .with_for_update()
        )
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                        detail="Only pending or confirmed orders can be cancelled")
        
        await OrderService._restore_stock_for_order(db, order)
        order.status = OrderStatus.CANCELLED

        try:
           await db.commit()
        except Exception:
            logger.error("Order cancellation commit failed", extra={"order_id": order_id}, exc_info=True)
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Order cancellation failed")

        order_eagered = await db.scalar(select(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).where(
            Order.id==order.id))
        return order_eagered
