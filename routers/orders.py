from fastapi import APIRouter, status, Request
from schemas.orders import OrderOut
from utils.deps import db_dependency, active_user_dependency
from services.checkout import CheckoutService
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
    order = CheckoutService.checkout(db=db, user_id=current_user.id)

    logger.info("Checkout successful", extra={"user_id": current_user.id, "order_id": order.id})

    return order