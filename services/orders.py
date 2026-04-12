from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
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
    def get_orders(db: Session, user_id: int, limit: int, offset: int) -> tuple[list[Order], int]:
        """Return a paginated list of the user's orders and the total count.

        Orders are returned newest first. Total reflects all matching orders
        before pagination, used by the caller to build the response envelope.
        """
        query = db.query(Order).filter(Order.user_id==user_id).order_by(Order.created_at.desc())
        total = query.count()
        orders = query.offset(offset).limit(limit).all()

        return orders, total


    @staticmethod
    def get_order(db: Session, user_id: int, order_id: int) -> Order:
        """Return a single order with its items and products, enforcing ownership.

        Raises:
            HTTPException 404: If the order does not exist or belongs to another user.
        """
        order = db.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).filter(
            Order.user_id==user_id, Order.id==order_id
        ).first()

        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        return order


    @staticmethod
    def _restore_stock_for_order(db: Session, order: Order) -> None:
        """Restore stock for every item in the order and log inventory changes.
        
        Locks product rows in deterministic order (sorted by product_id) to
        prevent deadlocks. Does not commit — caller owns the transaction.
        """
        sorted_items = sorted(order.items, key=lambda item: item.product_id)
        for item in sorted_items:
            product = db.query(Product).filter(Product.id==item.product_id).with_for_update().first()
            product.stock += item.quantity
            inventory_change = InventoryChange(product_id=product.id, change_amount=item.quantity, reason=InventoryChangeReason.CANCELLATION)
            db.add(inventory_change)


    @staticmethod
    def cancel_order(db: Session, user_id: int, order_id: int):
        """Cancel a customer's pending order atomically — restore stock and log inventory.

        Policy: customers can only cancel PENDING orders. CONFIRMED+ requires admin.

        Raises 404 (not found / wrong owner), 409 (not pending), 500 (commit failure).
        """
        order = db.query(Order).filter(Order.user_id==user_id, Order.id==order_id).with_for_update().first()

        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending orders can be cancelled")
        
        OrderService._restore_stock_for_order(db, order)
        order.status = OrderStatus.CANCELLED

        try:
           db.commit()
        except Exception:
            logger.error("Order cancellation commit failed", extra={"user_id": user_id, "order_id": order_id}, exc_info=True)
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Order cancellation failed")

        order_eagered = db.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).filter(
            Order.user_id==user_id, Order.id==order.id).first()
        return order_eagered
    

    @staticmethod
    def get_all_orders(db: Session, limit: int, offset: int, status_filter: Optional[OrderStatus]=None) -> tuple[list[Order], int]:
        """Return a paginated list of all orders across all users for admin view.

        Optionally filters by order status. Orders are returned newest first.
        Total reflects all matching orders before pagination.
        """
        query = db.query(Order).order_by(Order.created_at.desc())
        if status_filter is not None:
            query = query.filter(Order.status == status_filter)
        total = query.count()
        orders = query.offset(offset).limit(limit).all()

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
    def update_order_status(db: Session, new_status: OrderStatus, order_id: int):
        """Advance an order through its lifecycle (PENDING→CONFIRMED→SHIPPED→COMPLETED).

        Locks the order row before validation to prevent TOCTOU races.
        Cancellation is not handled here — use cancel_order / admin_cancel_order.

        Raises 404 (not found), 409 (invalid/unchanged transition), 500 (commit failure).
        """
        order = db.query(Order).filter(Order.id==order_id).with_for_update().first()

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
           db.commit()
        except Exception:
            logger.error("Order status update commit failed", extra={"order_id": order_id}, exc_info=True)
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Order status update failed")

        order_eagered = db.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).filter(
            Order.id==order.id).first()
        return order_eagered


    @staticmethod
    def admin_cancel_order(db: Session, order_id: int) -> Order:
        """Cancel any non-terminal order atomically — restore stock and log inventory.

        Policy: admin can cancel PENDING and CONFIRMED orders (unlike customers, who
        can only cancel PENDING). No ownership check.

        Raises 404 (not found), 409 (already completed/cancelled), 500 (commit failure).
        """
        order = db.query(Order).filter(Order.id==order_id).with_for_update().first()
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                        detail="Only pending or confirmed orders can be cancelled")
        
        OrderService._restore_stock_for_order(db, order)
        order.status = OrderStatus.CANCELLED

        try:
           db.commit()
        except Exception:
            logger.error("Order cancellation commit failed", extra={"order_id": order_id}, exc_info=True)
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Order cancellation failed")

        order_eagered = db.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).filter(
            Order.id==order.id).first()
        return order_eagered
