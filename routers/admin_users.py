from fastapi import APIRouter, status, Request, Query
from models.enums import UserRole
from schemas.users import AdminUserListOut, AdminUserOut, UserRoleUpdate
from services.users import UserService
from utils.deps import db_dependency, admin_dependency
from middleware.rate_limiter import limiter
from utils.logger import get_logger
from typing import Optional

logger = get_logger(__name__)

router = APIRouter(
    prefix="/admin/users",
    tags=["admin-users"]
)


@router.get("/", response_model=AdminUserListOut, status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def get_all_users(request: Request,
                         db: db_dependency,
                         admin: admin_dependency,
                         limit: int = Query(ge=1, le=50, default=10),
                         offset: int = Query(ge=0, default=0),
                         role: Optional[UserRole] = None,
                         is_active: Optional[bool] = None):
    """Return a paginated list of all users. Optionally filter by role and/or is_active. Admin only."""
    users, total = await UserService.get_all_users(db, limit, offset, role, is_active)

    logger.info("Admin listed users", extra={"admin_id": admin.id, "count": len(users), "role": role, "is_active": is_active})

    return AdminUserListOut(items=users, limit=limit, offset=offset, total=total)


@router.get("/{user_id}", response_model=AdminUserOut, status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def get_user(request: Request, db: db_dependency, admin: admin_dependency, user_id: int):
    """Return a single user by ID. Admin only. Returns 404 if not found."""
    user = await UserService.get_user_by_id(db, user_id)

    logger.info("Admin fetched user", extra={"admin_id": admin.id, "target_user_id": user_id})

    return user


@router.patch("/{user_id}/deactivate", response_model=AdminUserOut, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def deactivate_user(request: Request, db: db_dependency, admin: admin_dependency, user_id: int):
    """Deactivate a user account and revoke all their sessions. Admin only. Returns 400 if self-targeting, 409 if already inactive."""
    user = await UserService.deactivate_user(db, user_id, admin.id)

    logger.info("Admin deactivated user", extra={"admin_id": admin.id, "target_user_id": user_id})

    return user      


@router.patch("/{user_id}/reactivate", response_model=AdminUserOut, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def reactivate_user(request: Request, db: db_dependency, admin: admin_dependency, user_id: int):
    """Reactivate a deactivated user account. Admin only. Returns 409 if already active."""
    user = await UserService.reactivate_user(db, user_id)

    logger.info("Admin reactivated user", extra={"admin_id": admin.id, "target_user_id": user_id})

    return user 


@router.patch("/{user_id}/role", response_model=AdminUserOut, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def update_user_role(request: Request, db: db_dependency, admin: admin_dependency, user_id: int, body: UserRoleUpdate):
    """Promote or demote a user's role. Admin only. Returns 400 if self-targeting, 409 if already has that role."""
    user = await UserService.update_user_role(db, user_id, body.role, admin.id)

    logger.info("Admin updated user role", extra={"admin_id": admin.id, "target_user_id": user_id, "new_role": body.role.value})

    return user     