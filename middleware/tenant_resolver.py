from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from core.database import SessionLocal
from sqlalchemy import select
from models.tenants import Tenant
from jose import jwt, JWTError
from core.config import settings
from core.redis_client import redis_client
from utils.logger import get_logger
from utils.tenant_cache import serialize_tenant, deserialize_tenant
import hashlib

logger = get_logger(__name__)

BYPASS_PATHS = frozenset({
    "/health",
    "/tenants/register",
    "/docs",
    "/redoc",
    "/openapi.json",
})
WEBHOOK_BYPASS_PREFIX = "/webhooks/stripe/"


class TenantResolverMiddleware(BaseHTTPMiddleware):
    """Resolve the tenant for every incoming request and store it in request.state.tenant."""

    async def _resolve_from_api_key(self, api_key: str, ip: str, path: str) -> Tenant | None:
        """Resolve tenant from X-Tenant-API-Key header using cache-aside; falls back to DB on miss."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        cache_key = f"tenant:apikey:{key_hash}"

        cached_data = await redis_client.redis.get(cache_key)
        if cached_data:
            logger.info("Cache HIT: Returning tenant from Redis", extra={"cache_key": cache_key, "source": "redis"})
            return deserialize_tenant(cached_data)

        logger.info("Cache MISS: Querying PostgreSQL for tenant", extra={"cache_key": cache_key, "source": "postgres"})
        async with SessionLocal() as db:
            tenant = await db.scalar(select(Tenant).where(Tenant.api_key_hash == key_hash))

        if tenant:
            await redis_client.redis.set(cache_key, serialize_tenant(tenant), ex=300)
        else:
            await redis_client.redis.incr(f"tenant:resolver:fail:{ip}")
            await redis_client.redis.expire(f"tenant:resolver:fail:{ip}", 60)
            logger.warning("Tenant resolver: invalid API key", extra={"ip": ip, "path": path})

        return tenant

    async def _resolve_from_jwt(self, token: str, ip: str, path: str) -> Tenant | None:
        """Resolve tenant from JWT Bearer token using cache-aside; falls back to DB on miss."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                logger.warning("Tenant resolver: JWT missing tenant_id claim", extra={"ip": ip, "path": path})
                return None

            cache_key = f"tenant:id:{tenant_id}"
            cached_data = await redis_client.redis.get(cache_key)
            if cached_data:
                logger.info("Cache HIT: Returning tenant from Redis", extra={"cache_key": cache_key, "source": "redis"})
                return deserialize_tenant(cached_data)

            logger.info("Cache MISS: Querying PostgreSQL for tenant", extra={"cache_key": cache_key, "source": "postgres"})
            async with SessionLocal() as db:
                tenant = await db.scalar(select(Tenant).where(Tenant.id == tenant_id))

            if tenant:
                await redis_client.redis.set(cache_key, serialize_tenant(tenant), ex=300)
            else:
                logger.warning("Tenant resolver: JWT tenant_id has no matching DB row", extra={"ip": ip, "path": path, "tenant_id": tenant_id})

            return tenant
        except JWTError:
            logger.warning("Tenant resolver: JWT decode failed", extra={"ip": ip, "path": path})
            return None

    async def dispatch(self, request: Request, call_next):
        """Orchestrate tenant resolution, enforce active status, and attach tenant to request state."""
        path = request.url.path
        if path in BYPASS_PATHS or path.startswith(WEBHOOK_BYPASS_PREFIX):
            return await call_next(request)

        ip = request.client.host
        fail_count = await redis_client.redis.get(f"tenant:resolver:fail:{ip}")
        if fail_count and int(fail_count) >= 10:
            logger.warning("Tenant resolver: IP rate limit exceeded", extra={"ip": ip, "path": path})
            return JSONResponse(status_code=429, content={"detail": "Too many failed attempts"})

        tenant_from_key = None
        tenant_from_jwt = None

        api_key = request.headers.get("X-Tenant-API-Key")
        if api_key:
            tenant_from_key = await self._resolve_from_api_key(api_key, ip, path)
            if not tenant_from_key:
                return JSONResponse(status_code=401, content={"detail": "Invalid API Key"})

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            tenant_from_jwt = await self._resolve_from_jwt(auth_header[7:], ip, path)

        if tenant_from_key and tenant_from_jwt:
            if tenant_from_key.id != tenant_from_jwt.id:
                logger.warning("Tenant resolver: tenant mismatch", extra={"ip": ip, "path": path})
                return JSONResponse(status_code=403, content={"detail": "Tenant mismatch"})

        tenant = tenant_from_key or tenant_from_jwt

        if not tenant:
            logger.warning("Tenant resolver: tenant could not be resolved", extra={"ip": ip, "path": path})
            return JSONResponse(status_code=401, content={"detail": "Tenant could not be resolved"})

        if not tenant.is_active:
            logger.warning("Tenant resolver: inactive tenant", extra={"ip": ip, "path": path, "tenant_id": str(tenant.id)})
            return JSONResponse(status_code=403, content={"detail": "Tenant is deactivated"})

        request.state.tenant = tenant
        return await call_next(request)
