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
            tenant_id = payload.get("tenant_id")
            if user_id and tenant_id:
                return f"{str(tenant_id)}:{str(user_id)}"
        except JWTError:
            pass

    return get_remote_address(request)

limiter = Limiter(
    key_func=get_user_id,
    enabled=settings.ENV != "testing",
    default_limits=["200/hour"],
    storage_uri=settings.REDIS_URL
)