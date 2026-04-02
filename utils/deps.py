from core.database import SessionLocal
from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from starlette import status
from core.config import settings
from services.auth import AuthService
from models.users import User
from models.enums import UserRole
from utils.logger import get_logger

logger = get_logger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="auth/token"))]):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        token_type: str = payload.get("type")

        if email is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate credentials.")

        if token_type != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid token type. Access token required.")

        return {"email": email, "user_id": user_id, "user_role": user_role}

    except JWTError:
        logger.warning("JWT validation failed - invalid or expired token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials.")


user_dependency = Annotated[dict, Depends(get_current_user)]


def get_current_active_user(db: db_dependency, user: user_dependency):
    current_user = AuthService.get_active_user_by_id(db=db, user_id=user.get("user_id"))

    if current_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return current_user


active_user_dependency = Annotated[User, Depends(get_current_active_user)]


def get_current_active_admin(db: db_dependency, current_user: active_user_dependency):
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            "Non-admin access attempt on admin endpoint",
            extra={"user_id": current_user.id, "email": current_user.email, "role": current_user.role}
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You do not have permission to perform this action.")
    
    return current_user


admin_dependency = Annotated[User, Depends(get_current_active_admin)]


def get_current_active_customer(db: db_dependency, current_user: active_user_dependency):
    if current_user.role != UserRole.CUSTOMER:
        logger.warning(
            "Non-customer access attempt on customer endpoint",
            extra={"user_id": current_user.id, "email": current_user.email, "role": current_user.role}
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You do not have permission to perform this action.")
    
    return current_user


customer_dependency = Annotated[User, Depends(get_current_active_customer)]