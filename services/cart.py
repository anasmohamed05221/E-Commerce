from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.orm import joinedload
from models.cart_items import CartItem
from models.products import Product
from decimal import Decimal
from utils.logger import get_logger

logger = get_logger(__name__)


class CartService:

    @staticmethod
    async def get_cart(db: AsyncSession, user_id: int) -> list[CartItem]:
        """Fetch all cart items for a user with product details eagerly loaded."""
        cart_items = (await db.scalars(select(CartItem).options(joinedload(CartItem.product)).where(CartItem.user_id==user_id))).all()
        return cart_items
    
    @staticmethod
    def calculate_cart_total_price(cart_items: list[CartItem]) -> Decimal:
        """Calculate the total price of all items in the cart."""
        return sum((item.product.price * item.quantity for item in cart_items), start=Decimal("0"))
    
    @staticmethod
    async def add_to_cart(db: AsyncSession, user_id: int, product_id: int, quantity: int) -> CartItem:
        """Add a product to the user's cart, or increment quantity if already exists."""
        product = await db.scalar(select(Product).where(Product.id==product_id))
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        
        cart_item = await db.scalar(select(CartItem).options(joinedload(CartItem.product)).where(CartItem.user_id==user_id, CartItem.product_id==product_id))

        if cart_item:
            if cart_item.quantity + quantity > product.stock:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"message": "Not enough stock available",
                                                                                  "available_stock": product.stock})
            cart_item.quantity += quantity

        else:
            if quantity > product.stock:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"message": "Not enough stock available",
                                                                                   "available_stock": product.stock})
            cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)                                                                      
            db.add(cart_item)

        try:
            await db.commit()
        except Exception:
            logger.error("Add to cart commit failed", extra={"user_id": user_id, "product_id": product_id}, exc_info=True)
            await db.rollback()
            raise
        cart_item = await db.scalar(select(CartItem).options(joinedload(CartItem.product)).where(CartItem.user_id==user_id, CartItem.product_id==product_id))
        return cart_item

    @staticmethod
    async def update_cart_item(db: AsyncSession, user_id: int, product_id: int, new_quantity: int) -> CartItem:
        """Update the quantity of an existing cart item with stock validation."""
        cart_item = await db.scalar(select(CartItem).options(joinedload(CartItem.product)).where(CartItem.user_id==user_id, CartItem.product_id==product_id))
        if cart_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart Item not found.")
    
        if new_quantity > cart_item.product.stock:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"message": "Not enough stock available",
                                                                                  "available_stock": cart_item.product.stock})
        cart_item.quantity = new_quantity
        try:
            await db.commit()
        except Exception:
            logger.error("Update cart item commit failed", extra={"user_id": user_id, "product_id": product_id}, exc_info=True)
            await db.rollback()
            raise
        cart_item = await db.scalar(select(CartItem).options(joinedload(CartItem.product)).where(CartItem.user_id==user_id, CartItem.product_id==product_id))
        return cart_item
    

    @staticmethod
    async def clear_cart(db: AsyncSession, user_id: int):
        """Empty User's cart."""
        try:
            await db.execute(sa_delete(CartItem).where(CartItem.user_id == user_id))
            await db.commit()
        except Exception:
            logger.error("Clear cart commit failed", extra={"user_id": user_id}, exc_info=True)
            await db.rollback()
            raise


    @staticmethod
    async def remove_from_cart(db: AsyncSession, user_id: int, product_id: int):
        """Remove an item from the user's cart."""
        cart_item = await db.scalar(select(CartItem).where(CartItem.user_id==user_id, CartItem.product_id==product_id))

        if cart_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart Item not found.")
    
        await db.delete(cart_item)
        try:
            await db.commit()
        except Exception:
            logger.error("Remove from cart commit failed", extra={"user_id": user_id, "product_id": product_id}, exc_info=True)
            await db.rollback()
            raise