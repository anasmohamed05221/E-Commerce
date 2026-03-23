import redis.asyncio as aioredis
from core.config import settings

class RedisClient:
    def __init__(self):
        self.redis: aioredis.Redis | None = None

    async def connect(self):
        """Creates the connection pool when FastAPI starts."""
        self.redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True
            )
        
    async def disconnect(self):
        """Closes the connection pool when FastAPI shuts down."""
        if self.redis:
            await self.redis.aclose()


redis_client = RedisClient()