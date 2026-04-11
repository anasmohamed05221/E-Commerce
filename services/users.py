import secrets
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from models.users import User
from models.enums import UserRole
from services.email import send_email
from services.token import TokenService
from utils.hashing import verify_password, get_password_hash

from typing import Optional


class UserService:

    @staticmethod
    def request_password_change(db: Session, current_user: User, current_password: str, new_password: str, bg: BackgroundTasks) -> None:
        """Validate current password, store pending hash, and dispatch confirmation email."""
        if not verify_password(current_password, current_user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Incorrect current password")

        confirmation_token = secrets.token_urlsafe(32)

        current_user.pending_password_hash = get_password_hash(new_password)
        current_user.password_change_token = confirmation_token
        current_user.password_change_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        confirm_url = f"http://localhost:8000/users/confirm-password-change?token={confirmation_token}"
        deny_url = f"http://localhost:8000/users/deny-password-change?token={confirmation_token}"

        email_body = f"""
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

        bg.add_task(send_email, to_email=current_user.email,
                    subject="Confirm Password Change", body=email_body)


    @staticmethod
    def confirm_password_change(db: Session, token: str) -> None:
        """Apply pending password hash and revoke all sessions."""
        user = db.query(User).filter(
            User.password_change_token == token,
            User.password_change_expires_at > datetime.now(timezone.utc)
        ).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid or expired token")

        user.hashed_password = user.pending_password_hash
        user.pending_password_hash = None
        user.password_change_token = None
        user.password_change_expires_at = None

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        TokenService.revoke_all_user_tokens(user.id, db)


    @staticmethod
    def deny_password_change(db: Session, token: str, bg: BackgroundTasks) -> None:
        """Cancel pending password change, revoke all sessions, and send security alert."""
        user = db.query(User).filter(
            User.password_change_token == token
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
            db.rollback()
            raise

        TokenService.revoke_all_user_tokens(user.id, db)

        email_body = """
        A password change request for your account was denied.

        All active sessions have been logged out for security.

        If you did not request this change, please secure your account immediately.
        """

        bg.add_task(send_email, to_email=user.email,
                    subject="Security Alert: Password Change Denied", body=email_body)


    @staticmethod
    def deactivate_self(db: Session, current_user: User, password: str) -> None:
        """Verify password, deactivate account, and revoke all sessions."""
        if not verify_password(plain_password=password, hashed_password=current_user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Incorrect password")

        current_user.is_active = False
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        TokenService.revoke_all_user_tokens(current_user.id, db)


    @staticmethod
    def get_all_users(db: Session, limit: int, offset: int, role_filter: Optional[UserRole], is_active_filter: Optional[bool]) -> tuple[list[User], int]:
        query = db.query(User)
        if role_filter is not None:
            query = query.filter(User.role == role_filter)
        if is_active_filter is not None:
            query = query.filter(User.is_active == is_active_filter)

        total = query.count()
        users = query.offset(offset).limit(limit).all()

        return users, total
    

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return user
    

    @staticmethod
    def deactivate_user(db: Session, target_user_id: int, admin_id: int) -> User:
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
            db.rollback()
            raise

        TokenService.revoke_all_user_tokens(user.id, db)

        return user


    @staticmethod
    def reactivate_user(db: Session, target_user_id: int) -> User:
        user = db.query(User).filter(User.id == target_user_id).first()

        if user is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if user.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already active")
        
        user.is_active = True

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        
        return user

    @staticmethod
    def update_user_role(db: Session, target_user_id: int, new_role: UserRole, admin_id: int) -> User:
        if target_user_id == admin_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can't change your own role")
        
        user = db.query(User).filter(User.id == target_user_id).first()

        if user is None: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if user.role == new_role:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User already has the role: {new_role}")
        
        user.role = new_role

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        return user