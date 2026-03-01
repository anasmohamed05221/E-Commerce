from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional
from decimal import Decimal
from schemas.products import ProductListOut
from services.product_service import ProductService
from utils.deps import db_dependency
from middleware.rate_limiter import limiter


router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/", response_model=ProductListOut)
@limiter.limit("60/minute")
async def get_products(
    db: db_dependency,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category_id: Optional[int] = Query(default=None),
    min_price: Optional[Decimal] = Query(default=None, ge=0),
    max_price: Optional[Decimal] = Query(default=None, ge=0)
    ):
    if (min_price is not None and max_price is not None) and (min_price>max_price):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="min_price must be less than or equal to max_price")

    items, total = ProductService.get_products(db, limit, offset, category_id, min_price, max_price)

    return ProductListOut(items=items, limit=limit, offset=offset, total=total)
