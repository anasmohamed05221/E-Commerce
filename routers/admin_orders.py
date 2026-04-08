from fastapi import APIRouter, status, Request, Query
from models.enums import OrderStatus
from schemas.orders import AdminOrderListOut, AdminOrderOut, OrderStatusUpdate
from services.orders import OrderService
from utils.deps import db_dependency, admin_dependency
from middleware.rate_limiter import limiter
from utils.logger import get_logger
from typing import Optional

logger = get_logger(__name__)

router = APIRouter(
    prefix="/admin/orders",
    tags=["admin-orders"]
)

@router.get("/", response_model=AdminOrderListOut, status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def get_all_orders(request: Request,
                         db: db_dependency, 
                         admin: admin_dependency, 
                         limit: int = Query(ge=1, le=50, default=10), 
                         offset: int = Query(ge=0, default=0),
                         status_filter: Optional[OrderStatus] = Query(default=None, alias="status")):
    """Return a paginated list of all orders across all users. Admin only. Optionally filter by status."""
    orders, total = OrderService.get_all_orders(db, limit, offset, status_filter)

    logger.info("Admin orders listed", extra={"admin_id": admin.id, "count": len(orders), "status": status_filter})

    return AdminOrderListOut(items=orders, limit=limit, offset=offset, total=total)


@router.patch("/{order_id}/status", response_model=AdminOrderOut, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def update_order_status(request: Request, db: db_dependency, admin: admin_dependency, order_id: int,  body: OrderStatusUpdate):
    """Update an order's status. Admin only. Returns 404 if not found, 409 if the transition is invalid or unchanged."""
    order = OrderService.update_order_status(db, body.status, order_id)

    logger.info("Order status updated", extra={"admin_id": admin.id, "order_id": order_id, "new_status": body.status})
    
    return order