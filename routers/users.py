from fastapi import APIRouter, status, Request, BackgroundTasks
from utils.deps import db_dependency, active_user_dependency
from schemas.users import UserOut, PasswordChangeToken
from schemas.auth import ChangePasswordRequest, DeactivateUserRequest
from services.users import UserService
from middleware.rate_limiter import limiter
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
def get_user_info(request: Request, current_user: active_user_dependency, db: db_dependency):
    """Get current user info (protected endpoint)."""
    return current_user


@router.put("/me/password", status_code=status.HTTP_200_OK)
@limiter.limit("2/minute")
def change_password_request(request: Request, body: ChangePasswordRequest,
                                   current_user: active_user_dependency, db: db_dependency, bg: BackgroundTasks):
    """Request password change. Sends confirmation email."""
    UserService.request_password_change(db, current_user, body.current_password, body.new_password, bg)
    return {"message": "Confirmation email sent. Please check your inbox."}


@router.post("/confirm-password-change", status_code=status.HTTP_200_OK)
def confirm_password_change(token_body: PasswordChangeToken, db: db_dependency):
    """Confirm password change (public endpoint)."""
    UserService.confirm_password_change(db, token_body.token)
    return {"message": "Password updated successfully. Please login again."}


@router.post("/deny-password-change", status_code=status.HTTP_200_OK)
def deny_password_change(token_body: PasswordChangeToken, db: db_dependency, bg: BackgroundTasks):
    """Deny password change and logout all sessions (public endpoint)."""
    UserService.deny_password_change(db, token_body.token, bg)
    return {"message": "Password change cancelled. All sessions logged out."}


@router.delete("/deactivate", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
def deactivate_user(request: Request, body: DeactivateUserRequest,
                           current_user: active_user_dependency, db: db_dependency):
    """Deactivate user account and revoke all sessions (protected endpoint)."""
    UserService.deactivate_self(db, current_user, body.password)
    logger.info("User deactivated", extra={"user_id": current_user.id})
    return {"message": "Account deactivated"}