import secrets
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from models.users import User
from models.enums import UserRole
from services.email import send_email
from schemas.users import UpdateProfileRequest
from utils.email_templates import password_change_request_email, password_change_denied_email
from services.token import TokenService
from core.config import settings
from utils.hashing import verify_password, get_password_hash, hash_token

from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)


class UserService:

    @staticmethod
    def request_password_change(db: Session, current_user: User, current_password: str, new_password: str, bg: BackgroundTasks) -> None:
        """Validate current password, store pending hash, and dispatch confirmation email."""
        if not verify_password(current_password, current_user.hashed_password):
            logger.warning("Password change rejected — incorrect current password", extra={"user_id": current_user.id})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Incorrect current password")

        confirmation_token = secrets.token_urlsafe(32)

        current_user.pending_password_hash = get_password_hash(new_password)
        current_user.password_change_token = hash_token(confirmation_token)
        current_user.password_change_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        try:
            db.commit()
        except Exception:
            logger.error("Password change request commit failed", extra={"user_id": current_user.id}, exc_info=True)
            db.rollback()
            raise

        confirm_url = f"{settings.BASE_URL}/users/confirm-password-change?token={confirmation_token}"
        deny_url = f"{settings.BASE_URL}/users/deny-password-change?token={confirmation_token}"

        bg.add_task(send_email, to_email=current_user.email,
                    subject="Confirm Password Change",
                    body=password_change_request_email(confirm_url, deny_url))


    @staticmethod
    def confirm_password_change(db: Session, token: str) -> None:
        """Apply pending password hash and revoke all sessions."""
        user = db.query(User).filter(
            User.password_change_token == hash_token(token),
            User.password_change_expires_at > datetime.now(timezone.utc)
        ).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid or expired token")

        if not user.pending_password_hash:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid or expired token")

        user.hashed_password = user.pending_password_hash
        user.pending_password_hash = None
        user.password_change_token = None
        user.password_change_expires_at = None

        try:
            db.commit()
        except Exception:
            logger.error("Password change confirmation commit failed", extra={"user_id": user.id}, exc_info=True)
            db.rollback()
            raise

        TokenService.revoke_all_user_tokens(user.id, db)


    @staticmethod
    def deny_password_change(db: Session, token: str, bg: BackgroundTasks) -> None:
        """Cancel pending password change, revoke all sessions, and send security alert."""
        user = db.query(User).filter(
            User.password_change_token == hash_token(token)
        ).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid token")

        user.pending_password_hash = None
        user.password_change_token = None
        user.password_change_expires_at = None

        try:
            db.commit()
        except Exception:
            logger.error("Password change denial commit failed", extra={"user_id": user.id}, exc_info=True)
            db.rollback()
            raise

        TokenService.revoke_all_user_tokens(user.id, db)

        bg.add_task(send_email, to_email=user.email,
                    subject="Security Alert: Password Change Denied",
                    body=password_change_denied_email())


    @staticmethod
    def update_profile(db: Session, user: User, data: UpdateProfileRequest) -> User:
        """Partially update user profile (name, phone number)"""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        try:
            db.commit()
        except Exception:
            logger.error("Profile update commit failed", extra={"user_id": user.id}, exc_info=True)
            db.rollback()
            raise
        db.refresh(user)
        return user


    @staticmethod
    def deactivate_self(db: Session, current_user: User, password: str) -> None:
        """Verify password, deactivate account, and revoke all sessions."""
        if not verify_password(plain_password=password, hashed_password=current_user.hashed_password):
            logger.warning("Self-deactivation rejected — incorrect password", extra={"user_id": current_user.id})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Incorrect password")

        current_user.is_active = False
        try:
            db.commit()
        except Exception:
            logger.error("Self-deactivation commit failed", extra={"user_id": current_user.id}, exc_info=True)
            db.rollback()
            raise

        TokenService.revoke_all_user_tokens(current_user.id, db)


    @staticmethod
    def get_all_users(db: Session, limit: int, offset: int, role_filter: Optional[UserRole], is_active_filter: Optional[bool]) -> tuple[list[User], int]:
        """Return a paginated list of all users. Optionally filter by role and/or is_active."""
        query = db.query(User).order_by(User.id)
        if role_filter is not None:
            query = query.filter(User.role == role_filter)
        if is_active_filter is not None:
            query = query.filter(User.is_active == is_active_filter)

        total = query.count()
        users = query.offset(offset).limit(limit).all()

        return users, total
    

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Return a single user by ID. Raises 404 if not found."""
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return user
    

    @staticmethod
    def deactivate_user(db: Session, target_user_id: int, admin_id: int) -> User:
        """Deactivate a user account and revoke all their sessions. Admin cannot target themselves.

        Raises 400 (self-targeting), 404 (not found), 409 (already inactive).
        """
        if target_user_id == admin_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot deactivate their own account")
        
        user = db.query(User).filter(User.id == target_user_id).first()

        if user is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already inactive")
        
        user.is_active = False

        try:
            db.commit()
        except Exception:
            logger.error("User deactivation commit failed", extra={"target_user_id": target_user_id}, exc_info=True)
            db.rollback()
            raise

        TokenService.revoke_all_user_tokens(user.id, db)

        return user


    @staticmethod
    def reactivate_user(db: Session, target_user_id: int) -> User:
        """Reactivate a previously deactivated user account. Raises 404 (not found), 409 (already active)."""
        user = db.query(User).filter(User.id == target_user_id).first()

        if user is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if user.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already active")
        
        user.is_active = True

        try:
            db.commit()
        except Exception:
            logger.error("User reactivation commit failed", extra={"target_user_id": target_user_id}, exc_info=True)
            db.rollback()
            raise

        return user

    @staticmethod
    def update_user_role(db: Session, target_user_id: int, new_role: UserRole, admin_id: int) -> User:
        """Promote or demote a user's role. Admin cannot target themselves.

        Raises 400 (self-targeting), 404 (not found), 409 (already has role).
        """
        if target_user_id == admin_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can't change your own role")
        
        user = db.query(User).filter(User.id == target_user_id).first()

        if user is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if user.role == new_role:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User already has the role: {new_role.value}")
        
        user.role = new_role

        try:
            db.commit()
        except Exception:
            logger.error("Role update commit failed", extra={"target_user_id": target_user_id}, exc_info=True)
            db.rollback()
            raise

        return user