import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from jose import jwt, JWTError
from models.refresh_tokens import RefreshToken
from models.users import User
from core.config import settings
from services.auth_service import AuthService


class TokenService:
    """
    Handles all token operations: creation, validation, rotation, and revocation.
    """
    
    @staticmethod
    def create_access_token(email: str, user_id: int, role: str, expires_delta: timedelta = None):
        """
        Creates a JWT access token.
        
        Args:
            email: User's email
            user_id: User's ID
            role: User's role
            expires_delta: Token expiration time (default: 15 minutes)
        
        Returns:
            JWT access token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.now(timezone.utc) + expires_delta
        
        payload = {
            "sub": email,
            "id": user_id,
            "role": role,
            "type": "access",
            "exp": expire
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @staticmethod
    def create_refresh_token(email: str, user_id: int, role: str):
        """
        Creates a JWT refresh token.
        
        Args:
            email: User's email
            user_id: User's ID
            role: User's role
        
        Returns:
            Tuple of (refresh_token_string, jti)
        """
        # Generate unique JWT ID
        jti = secrets.token_urlsafe(32)
        
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": email,
            "id": user_id,
            "role": role,
            "jti": jti,
            "type": "refresh",
            "exp": expire
        }
        
        refresh_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        return refresh_token, jti, expire
    
    @staticmethod
    def create_tokens(email: str, user_id: int, role: str, db: Session):
        """
        Creates access token + refresh token pair.
        Stores refresh token in database.
        
        Args:
            email: User's email
            user_id: User's ID
            role: User's role
            db: Database session
        
        Returns:
            Dictionary with access_token, refresh_token, and token_type
        """
        # Create access token (15 minutes)
        access_token = TokenService.create_access_token(email, user_id, role)
        
        # Create refresh token (7 days)
        refresh_token, jti, expires_at = TokenService.create_refresh_token(email, user_id, role)
        
        # Hash the JTI and store in database
        token_hash = hashlib.sha256(jti.encode()).hexdigest()
        
        db_refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(db_refresh_token)
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def refresh_access_token(refresh_token: str, db: Session):
        """
        Validates refresh token and issues new access + refresh tokens.
        Implements token rotation (old token is revoked).
        
        Args:
            refresh_token: The refresh token to validate
            db: Database session
        
        Returns:
            Dictionary with new access_token, refresh_token, and token_type
        
        Raises:
            HTTPException: If token is invalid, expired, or revoked
        """
        
        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Validate token type
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            email = payload.get("sub")
            user_id = payload.get("id")
            role = payload.get("role")
            jti = payload.get("jti")
            
            if not all([email, user_id, role, jti]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Hash JTI and check database
            token_hash = hashlib.sha256(jti.encode()).hexdigest()
            db_token = db.query(RefreshToken).filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False
            ).first()
            
            if not db_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token not found or revoked"
                )
            
            # Check expiry
            if db_token.expires_at < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            user = db.query(User).filter(User.id == user_id).one_or_none()
            if not user.is_active:
                raise HTTPException(status_code=403, detail="Account is inactive")

            # Revoke old token (token rotation)
            db_token.revoked = True
            db.commit()
            
            # Create new token pair
            return TokenService.create_tokens(email, user_id, role, db)
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    @staticmethod
    def revoke_token(refresh_token: str, db: Session):
        """
        Revokes a refresh token (logout).
        
        Args:
            refresh_token: The refresh token to revoke
            db: Database session
        """
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            jti = payload.get("jti")
            
            if jti:
                token_hash = hashlib.sha256(jti.encode()).hexdigest()
                
                db_token = db.query(RefreshToken).filter(
                    RefreshToken.token_hash == token_hash
                ).first()
                
                if db_token:
                    db_token.revoked = True
                    db.commit()
                    
        except JWTError:
            pass  # Token already invalid, nothing to revoke
    
    @staticmethod
    def revoke_all_user_tokens(user_id: int, db: Session):
        """
        Revokes all refresh tokens for a user (logout from all devices).
        
        Args:
            user_id: The user's ID
            db: Database session
        """
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False
        ).update({"revoked": True})
        db.commit()
