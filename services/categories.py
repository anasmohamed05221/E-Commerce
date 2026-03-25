from sqlalchemy.orm import Session
from models.categories import Category
import json
from fastapi.encoders import jsonable_encoder
from core.redis_client import redis_client
from core.logging_config import get_logger

logger = get_logger(__name__)

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