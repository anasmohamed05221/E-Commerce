from fastapi import APIRouter, status, Request
from schemas.categories import CategoryCreate, CategoryUpdate, CategoryOut
from services.categories import CategoryService
from utils.deps import db_dependency, admin_dependency
from middleware.rate_limiter import limiter
from utils.logger import get_logger

logger = get_logger(__name__)

# async def is intentional here: service methods await Redis for cache invalidation
router = APIRouter(
    prefix="/admin/categories",
    tags=["admin-categories"]
)


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_category(request: Request, db: db_dependency, admin: admin_dependency, body: CategoryCreate):
    """Create a new category. Admin only."""
    category = await CategoryService.create_category(db, body.name, body.description)
    logger.info("Category created", extra={"admin_id": admin.id, "category_id": category.id})
    return category


@router.patch("/{category_id}", response_model=CategoryOut, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def update_category(request: Request, db: db_dependency, admin: admin_dependency, body: CategoryUpdate, category_id: int):
    """Partially update a category. Admin only."""
    category = await CategoryService.update_category(db, category_id, body.name, body.description)
    logger.info("Category updated", extra={"admin_id": admin.id, "category_id": category.id})
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_category(request: Request, db: db_dependency, admin: admin_dependency, category_id: int):
    """Delete a category. Admin only. Fails if any products are linked."""
    await CategoryService.delete_category(db, category_id)
    logger.info("Category deleted", extra={"admin_id": admin.id, "category_id": category_id})