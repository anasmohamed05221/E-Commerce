from fastapi import APIRouter, status, Request
from schemas.cart import CartOut, CartItemOut, CartItemCreate, CartItemUpdate
from utils.deps import db_dependency, customer_dependency
from services.cart import CartService
from middleware.rate_limiter import limiter
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/cart",
    tags=["cart"]
)


@router.get("/", response_model=CartOut, status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def get_cart(request: Request, db: db_dependency, current_user: customer_dependency):
    """
    View current user's cart (protected endpoint).
    """
    cart_items = await CartService.get_cart(db=db, user_id=current_user.id)
    total_price = CartService.calculate_cart_total_price(cart_items)

    cart = CartOut(cart_items=cart_items, total_price=total_price)

    return cart


@router.post("/", response_model=CartItemOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def add_to_cart(request: Request, db: db_dependency, current_user: customer_dependency, new_item: CartItemCreate):
    """
    Add item to current user's cart (protected endpoint).
    """
    cart_item = await CartService.add_to_cart(db=db, user_id=current_user.id, product_id=new_item.product_id,
                                        quantity=new_item.quantity)

    logger.info("Item added to cart", extra={"user_id": current_user.id, "product_id": new_item.product_id, "quantity": new_item.quantity})

    return cart_item


@router.patch("/{product_id}", response_model=CartItemOut, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def update_cart_item(request: Request, db: db_dependency, current_user: customer_dependency, product_id: int, update: CartItemUpdate):
    """
    Update item quantity (protected endpoint).
    """
    cart_item = await CartService.update_cart_item(db=db, user_id=current_user.id, product_id=product_id , new_quantity=update.quantity)

    logger.info("Cart item quantity updated", extra={"user_id": current_user.id, "product_id": product_id, "new_quantity": update.quantity})

    return cart_item


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def clear_cart(request: Request, db: db_dependency, current_user: customer_dependency):
    """Clear the user's cart."""

    await CartService.clear_cart(db, current_user.id)

    logger.info("Cart cleared", extra={"user_id": current_user.id})


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def remove_from_cart(request: Request, db: db_dependency, current_user: customer_dependency, product_id: int):
    """
    Remove item from cart
    """

    await CartService.remove_from_cart(db=db, user_id=current_user.id, product_id=product_id)

    logger.info("Item removed from cart", extra={"user_id": current_user.id, "product_id": product_id})