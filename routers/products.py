from fastapi import APIRouter, HTTPException, status, Request, Depends
from schemas.products import ProductListOut, ProductDetailOut, ProductFilterParams
from services.product_service import ProductService
from utils.deps import db_dependency
from middleware.rate_limiter import limiter


router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/", response_model=ProductListOut, status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def get_products(
    db: db_dependency, request: Request,
    filters: ProductFilterParams = Depends()
    ):
    """List products with optional filtering by category and price range."""
    items, total = ProductService.get_products(
        db, filters.limit, filters.offset, filters.category_id, filters.min_price, filters.max_price
    )

    return ProductListOut(items=items, limit=filters.limit, offset=filters.offset, total=total)


@router.get("/{product_id}", response_model=ProductDetailOut, status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def get_product_details(db: db_dependency, request: Request, product_id: int):
    """Get detailed product information by ID."""
    product = ProductService.get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product