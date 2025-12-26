from utils.hashing import verify_password, get_password_hash
from models.users import User
from schemas.auth_schemas import CreateUserRequest
from sqlalchemy.orm import Session
from utils.verification import generate_verification_code, get_code_expiry_time
from services.email_service import send_email
from fastapi import HTTPException, BackgroundTasks
from starlette import status
from utils.logger import get_logger
from schemas.auth_schemas import VerifyEmailRequest
from datetime import datetime, timezone

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
        db.commit()

        subject = "Verify Your Email - E-commerce App"
        email_body=f"""
        <html>
        <body>
            <h2>Welcome to E-Commerce App!</h2>
            <p>Your verification code is:</p>
            <h1 style="color: #4CAF50; font-size: 32px;">{code}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
            """
        bg.add_task(send_email, to_email=request.email, subject=subject, body=email_body)

        db.refresh(model)
        return model


    @staticmethod
    def authenticate_user(email: str, password: str, db: Session):
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

        if user.verification_code_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired")

        user.is_verified = True
        user.verification_code = user.verification_code_expires_at = None

        db.add(user)
        db.commit()

        return user
    @staticmethod
    def get_active_user_by_id(db: Session, user_id: int) -> User | None:
        model = db.query(User).filter(User.id == user_id, User.is_active == True).one_or_none()

        return model