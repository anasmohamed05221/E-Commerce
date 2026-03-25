from fastapi import APIRouter, Request, HTTPException, status
from schemas.categories import CategoryOut
from services.categories import CategoryService
from utils.deps import db_dependency
from middleware.rate_limiter import limiter


router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)

@router.get("/", response_model=list[CategoryOut], status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def get_categories(db: db_dependency, request: Request):
    """List all product categories."""
    categories = await CategoryService.get_categories(db)
    return categories