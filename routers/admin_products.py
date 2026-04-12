from fastapi import APIRouter, status, Request
from schemas.products import ProductCreate, ProductDetailOut, ProductUpdate
from services.products import ProductService
from utils.deps import db_dependency, admin_dependency
from middleware.rate_limiter import limiter
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/admin/products",
    tags=["admin-products"]
)


@router.post("/", response_model= ProductDetailOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_product(request: Request, db: db_dependency, admin: admin_dependency, body: ProductCreate):
    """Create a new product. Admin only."""
    product = ProductService.create_product(db, body)
    logger.info("Product created", extra={"admin_id": admin.id, "product_id": product.id})
    return product


@router.patch("/{product_id}", response_model= ProductDetailOut, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
def update_product(request: Request, db: db_dependency, admin: admin_dependency, body: ProductUpdate, product_id: int):
    """Update an existing product. Admin only."""
    product = ProductService.update_product(db, body, product_id)
    logger.info("Product updated", extra={"admin_id": admin.id, "product_id": product.id})
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
def delete_product(request: Request, db: db_dependency, admin: admin_dependency, product_id: int):
    """Delete an existing product. Admin only."""
    ProductService.delete_product(db, product_id)
    logger.info("Product deleted", extra={"admin_id": admin.id, "product_id": product_id})
