from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from utils.deps import db_dependency, user_dependency
from starlette import status
from schemas.auth_schemas import (Token, VerifyEmailRequest, CreateUserRequest, ForgotPasswordRequest
,RevokeTokenRequest, RefreshTokenRequest, ResetPasswordRequest)
from services.auth_service import AuthService
from services.token_service import TokenService
from models.users import User
from datetime import datetime, timezone
from utils.hashing import get_password_hash
from services.email_service import send_email
from pydantic import EmailStr
import secrets
from datetime import datetime, timezone, timedelta
from middleware.rate_limiter import limiter
from utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)



@router.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login_for_access_token(request: Request, db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    user = AuthService.authenticate_user(form_data.username, form_data.password, db)

    if not user:
        # Log failed login attempt
        logger.warning(
            "Login failed - invalid credentials",
            extra={"email": form_data.username}
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate user.")
    
    token = TokenService.create_tokens(user.email, user.id, user.role, db)

    # Log successful login
    logger.info(
        "User logged in successfully",
        extra={"user_id": user.id, "email": user.email}
    )

    return token


@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def create_user(request: Request, body: CreateUserRequest, db: db_dependency, bg: BackgroundTasks):
    user = AuthService.create_user(body, db, bg)

    logger.info(
        "User registered successfully",
        extra={"user_id": user.id, "email": user.email}
    )

    return {"message": "Registration successful. Please check your email for verification code."}


@router.post("/verify", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
def verify_email(request: Request, body: VerifyEmailRequest, db: db_dependency):
    """
    Verifies user's email with the provided code.
    
    Checks:
    - User exists
    - Not already verified
    - Code matches
    - Code not expired
    """
    user = db.query(User).filter(body.email == User.email).first()

    if not user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")

    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail="Email already verified")

    if body.code != user.verification_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid verification code")

    if user.verification_code_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail="Verification code expired")

    user.is_verified = True
    user.verification_code = user.verification_code_expires_at = None

    db.add(user)
    db.commit()

    # Log successful verification
    logger.info(
        "Email verified successfully",
        extra={"user_id": user.id, "email": body.email}
    )

    return {"message": "Email verified successfully"}



@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
async def refresh_token(request: Request, body: RefreshTokenRequest, db: db_dependency):
    """
    Get new access token using refresh token.
    """
    token = TokenService.refresh_access_token(body.refresh_token, db)

    # Log token refresh (extract user_id from token if available)
    logger.info("Access token refreshed")

    return token


@router.post("/logout", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def logout(request: Request, body: RevokeTokenRequest, db: db_dependency):
    """
    Revoke refresh token (logout).
    """
    TokenService.revoke_token(body.refresh_token, db)

    logger.info("User logged out")

    return {"message": "Logged out successfully"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def forgot_password_request(request: Request, body: ForgotPasswordRequest, db: db_dependency, bg: BackgroundTasks):
    """
    Request password reset. via email.
    """
    model = db.query(User).filter(body.email == User.email).first()
    
    if not model:
        logger.info("Password reset requested for non-existent email",
        extra= {"email": body.email})
        return {"message": "If that email exists, a reset link has been sent."}

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Store token
    model.password_reset_token = reset_token
    model.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    db.commit()

    # Send reset email
    reset_url = f"http://localhost:8000/auth/reset-password?token={reset_token}"

    
    to_email=model.email
    subject="Reset Your Password"
    email_body=f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">Password Reset Request</h2>
            <p>We received a request to reset your password.</p>
            
            <div style="margin: 30px 0;">
                <p>Click the button below to reset your password:</p>
                <a href="{reset_url}" 
                style="display: inline-block; padding: 14px 28px; background-color: #3498db; 
                        color: white; text-decoration: none; border-radius: 4px; margin: 10px 0;
                        font-weight: bold;">
                    Reset Password
                </a>
            </div>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                ⏰ This link expires in 15 minutes.
            </p>
            
            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin: 20px 0;">
                <p style="margin: 0; color: #856404;">
                    <strong>⚠️ Security Notice:</strong> If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
                </p>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            
            <p style="color: #999; font-size: 12px;">
                If you're having trouble clicking the button, copy and paste this URL into your browser:
                <br><br>
                {reset_url}
            </p>
        </div>
    </body>
    </html>
    """

    bg.add_task(send_email, to_email=to_email, subject=subject, body=email_body)
    
    logger.info(
        "Password reset email sent",
        extra={"user_id": model.id, "email": model.email}
    )

    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def reset_password(request: Request, body: ResetPasswordRequest, db: db_dependency):
    """
    Reset Password (public endpoint).
    """
    # Find user with this token
    model = db.query(User).filter(
        User.password_reset_token == body.token,
        User.password_reset_expires_at > datetime.now(timezone.utc)
    ).first()
    
    if not model:
        logger.warning("Password reset failed - invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Update password
    model.hashed_password = get_password_hash(body.new_password)
    
    # Clear pending change fields
    model.password_reset_token = None
    model.password_reset_expires_at = None
    
    db.commit()
    
    # Revoke all refresh tokens (force re-login everywhere)
    TokenService.revoke_all_user_tokens(model.id, db)

    logger.info(
        "Password reset successfully",
        extra={"user_id": model.id, "email": model.email}
    )
    
    return {"message": "Password updated successfully. Please login again."}

