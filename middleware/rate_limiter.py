from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from jose import jwt, JWTError
from core.config import settings

def get_user_id(request: Request):
    token = request.headers.get("Authorization")
    if token:
        try:
            token = token.replace("Bearer ", "")
            # Decode JWT
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("id")
            if user_id:
                return str(user_id)
        except JWTError:
            pass

    return get_remote_address(request)

limiter = Limiter(
    key_func=get_user_id,
    default_limits=["200/hour"]
)