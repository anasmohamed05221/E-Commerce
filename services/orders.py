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
    def cancel_order(db: Session, user_id: int, order_id: int):
        """Cancel a pending order, restore stock, and log inventory changes atomically.

        Locks the order row to prevent concurrent double-cancellation. Locks each
        product row before restoring stock. The entire operation is a single
        transaction — if any step fails, all changes roll back.

        Raises:
            HTTPException 404: If the order does not exist or belongs to another user.
            HTTPException 409: If the order status is not PENDING.
            HTTPException 500: If the transaction commit fails.
        """
        order = db.query(Order).filter(Order.user_id==user_id, Order.id==order_id).with_for_update().first()

        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending orders can be cancelled")
        
        sorted_items = sorted(order.items, key=lambda item: item.product_id)
        for item in sorted_items:
            product = db.query(Product).filter(Product.id==item.product_id).with_for_update().first()
            product.stock += item.quantity
            inventory_change = InventoryChange(product_id=product.id, change_amount=item.quantity, reason=InventoryChangeReason.CANCELLATION)
            db.add(inventory_change)
        order.status = OrderStatus.CANCELLED

        try:
           db.commit()
        except Exception:
            logger.error("Order cancellation commit failed", extra={"user_id": user_id, "order_id": order_id})
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Order cancellation failed")

        logger.info("Order cancelled successfully", extra={"user_id": user_id, "order_id": order_id})

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
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.COMPLETED, OrderStatus.CANCELLED]
        }

        if current_status not in allowed_transitions.keys():
            return False
        return new_status in allowed_transitions[current_status]
    
    
    @staticmethod
    def update_order_status(db: Session, new_status: OrderStatus, order_id: int):
        """Update an order's status with FSM validation and concurrency safety.

        Locks the order row before validation to prevent TOCTOU races. If
        transitioning to CANCELLED, restores stock and logs inventory changes
        atomically. Product rows are locked in deterministic order to prevent
        deadlocks.

        Raises:
            HTTPException 404: If the order does not exist.
            HTTPException 409: If the transition is invalid or status is unchanged.
            HTTPException 500: If the transaction commit fails.
        """
        order = db.query(Order).filter(Order.id==order_id).with_for_update().first()

        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        if order.status == new_status:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Order status is already '{new_status}'")
        
        if not OrderService._is_allowed_status_transition(order.status, new_status):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Transition from '{order.status}' to '{new_status}' is not allowed"
            )
        if new_status == OrderStatus.CANCELLED:
            sorted_items = sorted(order.items, key=lambda item: item.product_id)
            for item in sorted_items:
                product = db.query(Product).filter(Product.id==item.product_id).with_for_update().first()
                product.stock += item.quantity
                inventory_change = InventoryChange(product_id=product.id, change_amount=item.quantity, reason=InventoryChangeReason.CANCELLATION)
                db.add(inventory_change)

        order.status = new_status
        try:
           db.commit()
        except Exception:
            logger.error("Order status update commit failed", extra={"order_id": order_id})
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Order status update failed")

        logger.info(f"Order status updated to {new_status} successfully", extra={"order_id": order_id})

        order_eagered = db.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).filter(
            Order.id==order.id).first()
        return order_eagered

