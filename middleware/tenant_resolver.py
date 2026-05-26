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

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in BYPASS_PATHS or path.startswith(WEBHOOK_BYPASS_PREFIX):
            return await call_next(request)
        
        ip = request.client.host
        fail_key = f"tenant:resolver:fail:{ip}"
        fail_count = await redis_client.redis.get(fail_key)
        if fail_count and int(fail_count) >= 10:
            logger.warning("Tenant resolver: IP rate limit exceeded", extra={"ip": ip, "path": path})
            return JSONResponse(status_code=429, content={"detail": "Too many failed attempts"})
        
        tenant_from_key = None
        tenant_from_jwt = None

        async with SessionLocal() as db:
            api_key = request.headers.get("X-Tenant-API-Key")
            if api_key:
                key_hash = hashlib.sha256(api_key.encode()).hexdigest()
                tenant_from_key = await db.scalar(
                    select(Tenant).where(Tenant.api_key_hash == key_hash)
                )
                if not tenant_from_key:
                    await redis_client.redis.incr(fail_key)
                    await redis_client.redis.expire(fail_key, 60)
                    logger.warning("Tenant resolver: invalid API key", extra={"ip": ip, "path": path})
                    return JSONResponse(status_code=401, content={"detail": "Invalid API Key"})
            
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                try:
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                    tenant_id = payload.get("tenant_id")
                    if tenant_id:
                        tenant_from_jwt = await db.scalar(
                            select(Tenant).where(Tenant.id == tenant_id)
                        )
                except JWTError:
                    pass

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