from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from models.orders import Order
from models.order_items import OrderItem
from models.enums import OrderStatus, InventoryChangeReason
from models.inventory_changes import InventoryChange
from models.products import Product
from utils.logger import get_logger

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
        
        for item in order.items:
            product = db.query(Product).filter(Product.id==item.product.id).with_for_update().first()
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