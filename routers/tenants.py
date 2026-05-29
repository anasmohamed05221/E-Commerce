from fastapi import APIRouter, Request, status
from schemas.tenants import TenantRegisterRequest, TenantRegisterOut, TenantRotateOut, TenantRevokeOut
from services.tenants import TenantService
from utils.deps import db_dependency, tenant_dependency
from middleware.rate_limiter import limiter
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"]
)

@router.post("/register", response_model=TenantRegisterOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register_tenant(db: db_dependency, request: Request, body: TenantRegisterRequest):
    """Register a new tenant and return a one-time plaintext API key."""
    tenant_obj, api_key_plaintext = await TenantService.register_tenant(db, body.name, body.slug,
                                                                        body.email, body.password, body.plan)
    logger.info("Tenant registered", extra={"tenant_id": str(tenant_obj.id), "slug": tenant_obj.slug})
    return TenantRegisterOut(
                id=tenant_obj.id,
                name=tenant_obj.name,
                slug=tenant_obj.slug,
                plan=tenant_obj.plan,
                is_active=tenant_obj.is_active,
                created_at=tenant_obj.created_at,
                api_key=api_key_plaintext,
                message="Tenant created successfully. Save your API key now, it will not be shown again. The owner account was automatically registered as the tenant administrator and can log in to the store using the same credentials."
            )

@router.post("/me/rotate-api-key", response_model=TenantRotateOut, status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def rotate_api_key(db: db_dependency, request: Request, tenant: tenant_dependency):
    """Rotate the current tenant's API key and return the new plaintext key exactly once."""
    new_plaintext = await TenantService.rotate_api_key(db, tenant)
    logger.info("API key rotated", extra={"tenant_id": str(tenant.id)})
    return TenantRotateOut(api_key=new_plaintext, message="New API key issued. Save it now, it will not be shown again.")


@router.delete("/me/api-key", response_model=TenantRevokeOut, status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def revoke_api_key(db: db_dependency, request: Request, tenant: tenant_dependency):
    """Revoke the current tenant's API key; tenant remains active and can still authenticate via JWT."""
    await TenantService.revoke_api_key(db, tenant)
    logger.info("API key revoked", extra={"tenant_id": str(tenant.id)})
    return TenantRevokeOut(message="API key revoked. Use your credentials to log in and rotate a new key.")