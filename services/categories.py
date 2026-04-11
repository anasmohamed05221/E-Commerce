from sqlalchemy.orm import Session
from models.categories import Category
from models.products import Product
from fastapi import HTTPException, status
from typing import Optional
import json
from fastapi.encoders import jsonable_encoder
from core.redis_client import redis_client
from core.logging_config import get_logger

logger = get_logger(__name__)

CACHE_KEY = "categories:all"

class CategoryService:
    @staticmethod
    async def get_categories(db: Session) -> list[Category]:
        """Fetch all categories, using Redis cache when available."""
        cache_key = "categories:all"

        # Ask Redis if it has the data
        cached_data = await redis_client.redis.get(cache_key)
        
        if cached_data:
            logger.info(
                "Cache HIT: Returning categories from Redis", 
                extra={"cache_key": cache_key, "source": "redis"}
            )
            # Deserialize the JSON string back into a Python list
            return json.loads(cached_data)

        logger.info(
            "Cache MISS: Querying PostgreSQL", 
            extra={"cache_key": cache_key, "source": "postgres"}
        )
        categories = db.query(Category).order_by(Category.name.asc()).all()

        # Serialize the data
        # jsonable_encoder cleanly removes SQLAlchemy metadata and converts dates to strings
        json_friendly_data = jsonable_encoder(categories)
        
        # 4. Save to Redis (ex=3600 -> expire after 1 hour)
        await redis_client.redis.set(
            cache_key,
            json.dumps(json_friendly_data),
            ex=3600
        )
        return categories

    @staticmethod
    async def create_category(db: Session, name: str, description: Optional[str]) -> Category:
        """Create a new category. Raises 409 if name already exists."""
        existing = db.query(Category).filter(Category.name == name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{name}' already exists."
            )

        category = Category(name=name, description=description)
        db.add(category)

        try:
            db.commit()
            db.refresh(category)
        except Exception:
            logger.error("Category create commit failed", extra={"name": name}, exc_info=True)
            db.rollback()
            raise

        await redis_client.redis.delete(CACHE_KEY)

        return category

    @staticmethod
    async def update_category(db: Session, category_id: int, name: Optional[str], description: Optional[str]) -> Category:
        """Partial update a category. Raises 400 if no fields provided, 404 if not found, 409 if new name is taken."""
        if name is None and description is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field (name or description) must be provided."
            )

        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found."
            )

        if name is not None:
            conflict = (
                db.query(Category)
                .filter(Category.name == name, Category.id != category_id)
                .first()
            )
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Category '{name}' already exists."
                )
            category.name = name

        if description is not None:
            category.description = description

        try:
            db.commit()
            db.refresh(category)
        except Exception:
            logger.error("Category update commit failed", extra={"category_id": category_id}, exc_info=True)
            db.rollback()
            raise

        await redis_client.redis.delete(CACHE_KEY)

        return category

    @staticmethod
    async def delete_category(db: Session, category_id: int) -> None:
        """Delete a category. Raises 404 if not found, 409 if any products are linked."""
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found."
            )

        linked_product = db.query(Product).filter(Product.category_id == category_id).first()
        if linked_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category has linked products. Reassign or delete them before removing this category."
            )

        db.delete(category)

        try:
            db.commit()
        except Exception:
            logger.error("Category delete commit failed", extra={"category_id": category_id}, exc_info=True)
            db.rollback()
            raise

        await redis_client.redis.delete(CACHE_KEY)