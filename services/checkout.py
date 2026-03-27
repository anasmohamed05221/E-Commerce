from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.orders import Order
from models.order_items import OrderItem
from models.cart_items import CartItem
from services.cart import CartService
from models.inventory_changes import InventoryChange

class CheckoutService:
    @staticmethod
    def _validate_cart(db: Session, user_id: int) -> list[CartItem]:
        """Fetch cart items and verify cart is non-empty with sufficient stock.

        Raises:
            HTTPException 400: If cart is empty.
            HTTPException 409: If any item exceeds available stock.
        """
        cart_items = CartService.get_cart(db, user_id)
        if len(cart_items)==0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail="Can't checkout while cart is empty")
        
        for item in cart_items:
            product = item.product
            if item.quantity > product.stock:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                                    detail={"message": "Not enough stock available",
                                                    "product_id": product.id,
                                                    "product_name": product.name,
                                                    "available_stock": product.stock})
        return cart_items


    @staticmethod
    def _process_cart_items(cart_items: list[CartItem], order: Order) -> tuple[list[OrderItem], list[InventoryChange]]:
        """Create order items and inventory change records from cart items.

        Snapshots product price at time of purchase, decrements product stock,
        and records each stock change as an inventory audit entry.
        """
        order_items = []
        inventory_changes = []
        for item in cart_items:
            product = item.product
            order_item = OrderItem(order_id=order.id, product_id=product.id, price_at_time=product.price, 
                                   quantity=item.quantity, subtotal=(product.price*item.quantity))
            order_items.append(order_item)
            inventory_change = InventoryChange(product_id=product.id, change_amount=-item.quantity, reason="sale")
            inventory_changes.append(inventory_change)
            product.stock -= item.quantity
        return (order_items, inventory_changes)


    @staticmethod
    def checkout(db: Session, user_id: int) -> Order:
        """Execute the full checkout flow as a single atomic transaction.

        Validates cart, creates order with items, decrements stock,
        logs inventory changes, and clears the cart.
        """
        # Fetch user's cart items
        cart_items = CheckoutService._validate_cart(db, user_id)
        # Create order
        total_amount = CartService.calculate_cart_total_price(cart_items)
        order = Order(user_id=user_id, total_amount=total_amount, status="pending")
        db.add(order)
        db.flush()

        # Create order items and inventory changes
        order_items, inventory_changes = CheckoutService._process_cart_items(cart_items, order)
        
        # Checkout
        for order_item, inventory_change, cart_item in zip(order_items, inventory_changes, cart_items):
            db.add(order_item)
            db.add(inventory_change)
            db.delete(cart_item)
        
        db.commit()
        return order

        