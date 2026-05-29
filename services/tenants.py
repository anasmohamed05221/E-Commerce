import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from utils.hashing import hash_token, get_password_hash
from models.tenants import Tenant
from models.users import User
from models.enums import PlanTier, UserRole
from utils.logger import get_logger
from core.redis_client import redis_client
from redis.exceptions import RedisError

logger = get_logger(__name__)


class TenantService:
    """Handles tenant registration and lifecycle operations."""

    @staticmethod
    def _generate_api_key() -> tuple[str, str]:
        """Generate a prefixed plaintext API key and its SHA256 hash; returns (plaintext, hash)."""
        plaintext = "vnx_" + secrets.token_urlsafe(32)
        return plaintext, hash_token(plaintext)

    @staticmethod
    async def register_tenant(db: AsyncSession, name: str, slug: str, email: str, password: str, plan: PlanTier) -> tuple[Tenant, str]:
        """Create a new tenant, hash credentials, and return the tenant with its plaintext API key."""
        api_key_plaintext, api_key_hash = TenantService._generate_api_key()

        password_hash = get_password_hash(password)

        tenant = Tenant(
            name=name,
            owner_email=email,
            owner_password_hash=password_hash,
            slug=slug,
            plan=plan,
            api_key_hash=api_key_hash,
            is_active=True,
        )
        
        try:
            db.add(tenant)
            await db.flush()

            user = User(
                tenant_id=tenant.id,
                email=email,
                first_name="Admin",
                last_name=name,
                hashed_password=password_hash,
                role=UserRole.ADMIN,
                is_verified=True,
            )
            db.add(user)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            logger.warning("Tenant registration conflict", extra={"slug": slug, "email": email})
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="slug already taken")
        except Exception:
            await db.rollback()
            logger.error("Tenant registration commit failed", extra={"slug": slug}, exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Tenant registration commit failed")

        await db.refresh(tenant)
        return tenant, api_key_plaintext
    
    @staticmethod
    async def rotate_api_key(db: AsyncSession, tenant: Tenant) -> str:
        """Rotate the tenant's API key atomically and invalidate both Redis cache entries."""
        old_hash = tenant.api_key_hash
        new_plaintext, new_hash = TenantService._generate_api_key()

        tenant_row = await db.scalar(select(Tenant).where(Tenant.id == tenant.id))

        tenant_row.api_key_hash = new_hash

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            logger.error("Tenant key rotation commit failed", extra={"tenant_id": str(tenant.id)}, exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Tenant key rotation commit failed")

        try:
            await redis_client.redis.delete(f"tenant:apikey:{old_hash}")
        except RedisError:
            logger.warning("API key cache invalidation failed", extra={"tenant_id": str(tenant.id)})

        try:
            await redis_client.redis.delete(f"tenant:id:{tenant.id}")
        except RedisError:
            logger.warning("Tenant cache invalidation failed", extra={"tenant_id": str(tenant.id)})
        

        return new_plaintext


    @staticmethod
    async def revoke_api_key(db: AsyncSession, tenant: Tenant) -> None:
        """Revoke the tenant's API key and invalidate both Redis cache entries."""
        if tenant.api_key_hash is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No API key to revoke")
        
        old_hash = tenant.api_key_hash

        tenant_row = await db.scalar(select(Tenant).where(Tenant.id == tenant.id))


        tenant_row.api_key_hash = None

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            logger.error("Tenant key revocation commit failed", extra={"tenant_id": str(tenant.id)}, exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Tenant key revocation commit failed")

        try:
            await redis_client.redis.delete(f"tenant:apikey:{old_hash}")
        except RedisError:
            logger.warning("API key cache invalidation failed", extra={"tenant_id": str(tenant.id)})

        try:
            await redis_client.redis.delete(f"tenant:id:{tenant.id}")
        except RedisError:
            logger.warning("Tenant cache invalidation failed", extra={"tenant_id": str(tenant.id)})