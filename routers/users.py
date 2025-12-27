from fastapi import APIRouter, HTTPException, status, Request, BackgroundTasks
from utils.deps import user_dependency, db_dependency
from services.email_service import send_email
from models.users import User
from utils.hashing import verify_password, get_password_hash
from schemas.auth_schemas import ChangePasswordRequest, DeactivateUserRequest
from services.token_service import TokenService
from services.auth_service import AuthService
from datetime import datetime, timezone, timedelta
import secrets
from middleware.rate_limiter import limiter
from utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)


router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/me", status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_user_info(request: Request, user: user_dependency, db: db_dependency):
    """
    Get current user info (protected endpoint).
    """
    model = AuthService.get_active_user_by_id(db=db, user_id=user.get("user_id"))

    if not model:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": model.id,
        "email": model.email,
        "first_name": model.first_name,
        "last_name": model.last_name,
        "phone_number": model.phone_number
    }


@router.put("/me/password", status_code=status.HTTP_200_OK)
@limiter.limit("2/minute")
async def change_password_request(request: Request, body: ChangePasswordRequest,
    user: user_dependency, db: db_dependency, bg: BackgroundTasks):
    """
    Request password change. Sends confirmation email.
    """
    model = AuthService.get_active_user_by_id(db=db, user_id=user.get("user_id"))
    
    if not model:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(body.current_password, model.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect current password")

    # Generate confirmation token
    confirmation_token = secrets.token_urlsafe(32)
    
    # Store pending change
    model.pending_password_hash = get_password_hash(body.new_password)
    model.password_change_token = confirmation_token
    model.password_change_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    db.commit()

    # Send confirmation email
    confirm_url = f"http://localhost:8000/users/confirm-password-change?token={confirmation_token}"
    deny_url = f"http://localhost:8000/users/deny-password-change?token={confirmation_token}"

    
    to_email=model.email
    subject="Confirm Password Change"
    email_body=f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">Password Change Request</h2>
            <p>A password change was requested for your account.</p>
            
            <div style="margin: 30px 0;">
                <p><strong>If this was you:</strong></p>
                <a href="{confirm_url}" 
                style="display: inline-block; padding: 12px 24px; background-color: #4CAF50; 
                        color: white; text-decoration: none; border-radius: 4px; margin: 10px 0;">
                    ✓ Yes, Confirm Password Change
                </a>
            </div>
            
            <div style="margin: 30px 0;">
                <p><strong>If this was NOT you:</strong></p>
                <a href="{deny_url}" 
                style="display: inline-block; padding: 12px 24px; background-color: #f44336; 
                        color: white; text-decoration: none; border-radius: 4px; margin: 10px 0;">
                    ✗ No, Deny and Logout All Sessions
                </a>
            </div>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                ⏰ This link expires in 15 minutes.
            </p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            
            <p style="color: #999; font-size: 12px;">
                If you're having trouble clicking the buttons, copy and paste the URLs below into your browser:
                <br><br>
                Confirm: {confirm_url}
                <br>
                Deny: {deny_url}
            </p>
        </div>
    </body>
    </html>
    """
    bg.add_task(send_email, to_email=to_email, subject=subject, body=email_body)
    
    
    return {"message": "Confirmation email sent. Please check your inbox."}




@router.get("/confirm-password-change", status_code=status.HTTP_200_OK)
async def confirm_password_change(token: str, db: db_dependency):
    """
    Confirm password change (public endpoint).
    """
    # Find user with this token
    model = db.query(User).filter(
        User.password_change_token == token,
        User.password_change_expires_at > datetime.now(timezone.utc)
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Update password
    model.hashed_password = model.pending_password_hash
    
    # Clear pending change fields
    model.pending_password_hash = None
    model.password_change_token = None
    model.password_change_expires_at = None
    
    db.commit()
    
    # Revoke all refresh tokens (force re-login everywhere)
    TokenService.revoke_all_user_tokens(model.id, db)
    
    return {"message": "Password updated successfully. Please login again."}



@router.get("/deny-password-change", status_code=status.HTTP_200_OK)
async def deny_password_change(token: str, db: db_dependency, bg: BackgroundTasks):
    """
    Deny password change and logout all sessions (public endpoint).
    """
    # Find user with this token
    model = db.query(User).filter(
        User.password_change_token == token
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    
    # Clear pending change
    model.pending_password_hash = None
    model.password_change_token = None
    model.password_change_expires_at = None
    
    db.commit()
    
    # Revoke all refresh tokens (logout attacker)
    TokenService.revoke_all_user_tokens(model.id, db)
    
    # Send security alert email
    
    to_email=model.email
    subject="Security Alert: Password Change Denied"
    email_body="""
    A password change request for your account was denied.
    
    All active sessions have been logged out for security.
    
    If you did not request this change, please secure your account immediately.
    """
    
    bg.add_task(send_email, to_email=to_email, subject=subject, body=email_body)
    
    return {"message": "Password change cancelled. All sessions logged out."}




@router.delete("/deactivate", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def deactivate_user(request: Request, body: DeactivateUserRequest, user: user_dependency, db: db_dependency):
    model = AuthService.get_active_user_by_id(db, user.get("user_id"))

    if not model:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(plain_password=body.password, hashed_password=model.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect password")

    # Revoke all tokens to end user sessions
    TokenService.revoke_all_user_tokens(model.id, db)

    # Deactivate user
    model.is_active = False
    db.commit()

    logger.info("User Deactivated")

    return {"message": "Account deactivated"}
