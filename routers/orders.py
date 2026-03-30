from fastapi import APIRouter, status, Request, Query
from schemas.orders import OrderOut, OrderListOut
from utils.deps import db_dependency, active_user_dependency
from services.checkout import CheckoutService
from services.orders import OrderService
from middleware.rate_limiter import limiter
from utils.logger import get_logger

logger = get_logger(__name__)


router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)

@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def checkout(request: Request, db: db_dependency, current_user: active_user_dependency):
    """Place an order from the current user's active cart."""
    order = CheckoutService.checkout(db=db, user_id=current_user.id)

    logger.info("Checkout successful", extra={"user_id": current_user.id, "order_id": order.id})

    return order


@router.get("/", response_model=OrderListOut, status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def get_orders(request: Request,
                     db: db_dependency, 
                     current_user: active_user_dependency, 
                     limit: int = Query(ge=1, le=50, default=10), 
                     offset: int = Query(ge=0, default=0)):
    """Return a paginated list of the current user's orders, sorted by most recent."""
    orders, total = OrderService.get_orders(db=db, user_id=current_user.id, limit=limit, offset=offset)

    return OrderListOut(items=orders, limit=limit, offset=offset, total=total)


@router.get("/{order_id}", response_model=OrderOut, status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def get_order(request: Request, db: db_dependency, current_user: active_user_dependency, order_id: int):
    """Return full details for a single order, including all items. Returns 404 if not found or not owned by the user."""
    order = OrderService.get_order(db=db, user_id=current_user.id, order_id=order_id)

    return order


@router.post("/{order_id}/cancel", response_model=OrderOut, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def cancel_order(request: Request, db: db_dependency, current_user: active_user_dependency, order_id: int):
    """Cancel a pending order and restore stock for all items. Returns 409 if the order is not cancellable."""
    cancelled_order = OrderService.cancel_order(db=db, user_id=current_user.id, order_id=order_id)

    return cancelled_order