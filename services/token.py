import secrets
from utils.hashing import hash_token
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from jose import jwt, JWTError
from models.refresh_tokens import RefreshToken
from models.users import User
from core.config import settings


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
    async def create_tokens(email: str, user_id: int, role: str, db: AsyncSession):
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
        token_hash = hash_token(jti)
        
        db_refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(db_refresh_token)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    async def refresh_access_token(refresh_token: str, db: AsyncSession):
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
            token_hash = hash_token(jti)
            db_token = await db.scalar(select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False  # noqa: E712
            ))
            
            if not db_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token not found or revoked"
                )
            
            # Check expiry
            if db_token.expires_at.astimezone(timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            user = await db.scalar(select(User).where(User.id == user_id))
            if not user.is_active:
                raise HTTPException(status_code=403, detail="Account is inactive")

            # Revoke old token (token rotation)
            db_token.revoked = True
            try:
                await db.commit()
            except Exception:
                await db.rollback()
                raise

            # Create new token pair
            return await TokenService.create_tokens(email, user_id, role, db)
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    @staticmethod
    async def revoke_token(refresh_token: str, db: AsyncSession):
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
                token_hash = hash_token(jti)
                
                db_token = await db.scalar(select(RefreshToken).where(
                    RefreshToken.token_hash == token_hash
                ))
                
                if db_token:
                    db_token.revoked = True
                    try:
                        await db.commit()
                    except Exception:
                        await db.rollback()
                        raise

        except JWTError:
            pass  # Token already invalid, nothing to revoke
    
    @staticmethod
    async def revoke_all_user_tokens(user_id: int, db: AsyncSession):
        """
        Revokes all refresh tokens for a user (logout from all devices).
        
        Args:
            user_id: The user's ID
            db: Database session
        """
        try:
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)  # noqa: E712
                .values(revoked=True)
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
