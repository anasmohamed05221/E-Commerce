from utils.hashing import verify_password, get_password_hash, hash_token
from models.users import User
from schemas.auth import CreateUserRequest
from sqlalchemy.orm import Session
from utils.verification import generate_verification_code, get_code_expiry_time
from services.email import send_email
from utils.email_templates import verification_email, password_reset_email
from fastapi import HTTPException, BackgroundTasks
from starlette import status
from utils.logger import get_logger
from schemas.auth import VerifyEmailRequest
from datetime import datetime, timezone, timedelta
from core.config import settings
from services.token import TokenService
import secrets

logger = get_logger(__name__)

class AuthService:

    @staticmethod
    def create_user(request: CreateUserRequest, db: Session, bg: BackgroundTasks):
        """
        Creates a new user and sends verification email.
        
        Flow:
        1. Check if email already exists
        2. Generate verification code
        3. Create user (unverified)
        4. Send verification email
        5. Return success message
        """
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            # Log duplicate registration attempt
            logger.warning(
                "Registration attempt with existing email",
                extra={"email": request.email}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        code = generate_verification_code()
        expiry = get_code_expiry_time()

        model = User(
            email=request.email.lower().strip(), 
            first_name=request.first_name, 
            last_name=request.last_name,
            hashed_password=get_password_hash(request.password),
            phone_number=request.phone_number,
            is_verified=False,
            verification_code=code,
            verification_code_expires_at=expiry
        )

        db.add(model)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        subject = "Verify Your Email - E-commerce App"
        bg.add_task(send_email, to_email=request.email, subject=subject, body=verification_email(code))

        db.refresh(model)
        return model


    @staticmethod
    def authenticate_user(email: str, password: str, db: Session):
        """Authenticate a user by email and password."""
        user = db.query(User).filter(email==User.email).first()
        
        if not user:
            logger.warning(
            "Login failed - user not found",
            extra={"email": email}
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user.")
        
        if not user.is_active:
            logger.warning(
            "Login failed - inactive account",
            extra={"email": email}
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user.")
        
        if not verify_password(password, user.hashed_password):
            # Log failed password verification
            logger.warning(
                "Login failed - invalid password",
                extra={"user_id": user.id, "email": email}
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user.")

        if not user.is_verified:
            # Log unverified email attempt
            logger.warning(
                "Login attempt with unverified email",
                extra={"user_id": user.id, "email": email}
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox.")

        # Log successful authentication
        logger.debug(
            "User authenticated successfully",
            extra={"user_id": user.id, "email": email}
        )
            
        return user

    @staticmethod
    def verify_user(body: VerifyEmailRequest, db: Session):
        """Verify a user's email with the provided verification code."""
        user = db.query(User).filter(body.email == User.email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
            detail="Account inactive")

        if user.is_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified")

        if body.code != user.verification_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code")

        if user.verification_code_expires_at.astimezone(timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired")

        user.is_verified = True
        user.verification_code = user.verification_code_expires_at = None

        db.add(user)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        return user
    @staticmethod
    def get_active_user_by_id(db: Session, user_id: int) -> User | None:
        """Fetch an active user by ID, or return None if not found or inactive."""
        model = db.query(User).filter(User.id == user_id, User.is_active).one_or_none()

        return model

    @staticmethod
    def forgot_password(db: Session, email: str, bg: BackgroundTasks) -> None:
        """Generate a password reset token and dispatch a reset email.

        Silent no-op for unknown emails — prevents user enumeration.
        """
        model = db.query(User).filter(User.email == email).first()

        if not model:
            logger.info("Password reset requested for non-existent email", extra={"email": email})
            return

        reset_token = secrets.token_urlsafe(32)
        reset_token_hash = hash_token(reset_token)
        model.password_reset_token = reset_token_hash
        model.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        try:
            db.commit()
        except Exception:
            logger.error("Forgot password commit failed", extra={"email": email}, exc_info=True)
            db.rollback()
            raise

        reset_url = f"{settings.BASE_URL}/auth/reset-password?token={reset_token}"
        bg.add_task(send_email, to_email=model.email, subject="Reset Your Password", body=password_reset_email(reset_url))

        logger.info("Password reset email sent", extra={"user_id": model.id, "email": model.email})

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> None:
        """Apply a new password from a valid reset token and revoke all sessions.

        Raises:
            HTTPException 400: If token is invalid or expired.
        """
        model = db.query(User).filter(
            User.password_reset_token == hash_token(token),
            User.password_reset_expires_at > datetime.now(timezone.utc)
        ).first()

        if not model:
            logger.warning("Password reset failed — invalid or expired token")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

        model.hashed_password = get_password_hash(new_password)
        model.password_reset_token = None
        model.password_reset_expires_at = None

        try:
            db.commit()
        except Exception:
            logger.error("Reset password commit failed", extra={"user_id": model.id}, exc_info=True)
            db.rollback()
            raise

        TokenService.revoke_all_user_tokens(model.id, db)

        logger.info("Password reset successfully", extra={"user_id": model.id, "email": model.email})