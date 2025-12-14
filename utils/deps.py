from core.database import SessionLocal
from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from starlette import status
from core.config import settings
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials.")


user_dependency = Annotated[dict, Depends(get_current_user)]