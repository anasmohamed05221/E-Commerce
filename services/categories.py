from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.categories import Category
from models.products import Product
from fastapi import HTTPException, status
from typing import Optional
import json
from fastapi.encoders import jsonable_encoder
from core.redis_client import redis_client
from core.logging_config import get_logger
from redis.exceptions import RedisError
from uuid import UUID

logger = get_logger(__name__)

CACHE_KEY = "categories:all"

class CategoryService:
    @staticmethod
    async def get_categories(db: AsyncSession, tenant_id: UUID) -> list[Category]:
        """Fetch all categories, using Redis cache when available."""
        cache_key = f"tenant:{tenant_id}:{CACHE_KEY}"

        try:
            cached_data = await redis_client.redis.get(cache_key)
        except RedisError:
            logger.warning("Category cache read failed, falling back to DB", extra={"cache_key": cache_key})
            cached_data = None

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
        categories = (await db.scalars(select(Category).order_by(Category.name.asc()))).all()

        # Serialize the data
        # jsonable_encoder cleanly removes SQLAlchemy metadata and converts dates to strings
        json_friendly_data = jsonable_encoder(categories)
        
        try:
            await redis_client.redis.set(cache_key, json.dumps(json_friendly_data), ex=3600)
        except RedisError:
            logger.warning("Category cache write failed", extra={"cache_key": cache_key})
        return categories

    @staticmethod
    async def create_category(db: AsyncSession, tenant_id: UUID, name: str, description: Optional[str]) -> Category:
        """Create a new category. Raises 409 if name already exists."""
        existing = await db.scalar(select(Category).where(Category.name == name))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{name}' already exists."
            )

        category = Category(tenant_id=tenant_id, name=name, description=description)
        db.add(category)

        try:
            await db.commit()
            await db.refresh(category)
        except Exception:
            logger.error("Category create commit failed", extra={"name": name}, exc_info=True)
            await db.rollback()
            raise

        try:
            await redis_client.redis.delete(f"tenant:{tenant_id}:{CACHE_KEY}")
        except RedisError:
            logger.warning("Category cache invalidation failed", extra={"tenant_id": str(tenant_id)})

        return category

    @staticmethod
    async def update_category(db: AsyncSession, tenant_id: UUID, category_id: int, name: Optional[str], description: Optional[str]) -> Category:
        """Partial update a category. Raises 400 if no fields provided, 404 if not found, 409 if new name is taken."""
        if name is None and description is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field (name or description) must be provided."
            )

        category = await db.scalar(select(Category).where(Category.id == category_id))
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found."
            )

        if name is not None:
            conflict = await db.scalar(
                select(Category).where(Category.name == name, Category.id != category_id)
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
            await db.commit()
            await db.refresh(category)
        except Exception:
            logger.error("Category update commit failed", extra={"category_id": category_id}, exc_info=True)
            await db.rollback()
            raise

        try:
            await redis_client.redis.delete(f"tenant:{tenant_id}:{CACHE_KEY}")
        except RedisError:
            logger.warning("Category cache invalidation failed", extra={"tenant_id": str(tenant_id)})

        return category

    @staticmethod
    async def delete_category(db: AsyncSession, tenant_id: UUID, category_id: int) -> None:
        """Delete a category. Raises 404 if not found, 409 if any products are linked."""
        category = await db.scalar(select(Category).where(Category.id == category_id))
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found."
            )

        linked_product = await db.scalar(select(Product).where(Product.category_id == category_id))
        if linked_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category has linked products. Reassign or delete them before removing this category."
            )

        await db.delete(category)

        try:
            await db.commit()
        except Exception:
            logger.error("Category delete commit failed", extra={"category_id": category_id}, exc_info=True)
            await db.rollback()
            raise

        try:
            await redis_client.redis.delete(f"tenant:{tenant_id}:{CACHE_KEY}")
        except RedisError:
            logger.warning("Category cache invalidation failed", extra={"tenant_id": str(tenant_id)})