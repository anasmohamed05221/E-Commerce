from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from models.cart_items import CartItem
from models.products import Product
from decimal import Decimal


class CartService:

    @staticmethod
    def get_cart(db: Session, user_id: int) -> list[CartItem]:
        """Fetch all cart items for a user with product details eagerly loaded."""
        cart_items = db.query(CartItem).options(joinedload(CartItem.product)).filter(CartItem.user_id==user_id).all()
        return cart_items
    
    @staticmethod
    def calculate_cart_total_price(cart_items: list[CartItem]) -> Decimal:
        """Calculate the total price of all items in the cart."""
        return sum((item.product.price * item.quantity for item in cart_items), start=Decimal("0"))
    
    @staticmethod
    def add_to_cart(db: Session, user_id: int, product_id: int, quantity: int) -> CartItem:
        """Add a product to the user's cart, or increment quantity if already exists."""
        product = db.query(Product).filter(Product.id==product_id).first()
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        
        cart_item = db.query(CartItem).options(joinedload(CartItem.product)).filter(CartItem.user_id==user_id, CartItem.product_id==product_id).first()

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
            db.commit()
        except Exception:
            db.rollback()
            raise
        cart_item = db.query(CartItem).options(joinedload(CartItem.product)).filter(CartItem.user_id==user_id, CartItem.product_id==product_id).first()
        return cart_item

    @staticmethod
    def update_cart_item(db: Session, user_id: int, product_id: int, new_quantity: int) -> CartItem:
        """Update the quantity of an existing cart item with stock validation."""
        cart_item = db.query(CartItem).options(joinedload(CartItem.product)).filter(CartItem.user_id==user_id, CartItem.product_id==product_id).first()
        if cart_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart Item not found.")
    
        if new_quantity > cart_item.product.stock:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"message": "Not enough stock available",
                                                                                  "available_stock": cart_item.product.stock})
        cart_item.quantity = new_quantity
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        cart_item = db.query(CartItem).options(joinedload(CartItem.product)).filter(CartItem.user_id==user_id, CartItem.product_id==product_id).first()
        return cart_item
    

    @staticmethod
    def remove_from_cart(db: Session, user_id: int, product_id: int):
        """Remove an item from the user's cart."""
        cart_item = db.query(CartItem).filter(CartItem.user_id==user_id, CartItem.product_id==product_id).first()

        if cart_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart Item not found.")
    
        db.delete(cart_item)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise