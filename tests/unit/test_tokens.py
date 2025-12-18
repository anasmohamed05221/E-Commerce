from services.token_service import TokenService
from jose import jwt, JWTError
from core.config import settings
from datetime import timedelta
from time import sleep
import pytest

def test_access_token_creation():
    test_token = TokenService.create_access_token(email="user@example.com", user_id=1, role="customer")
    assert test_token

    payload = jwt.decode(test_token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "user@example.com"
    assert payload["id"] == 1
    assert payload["role"].lower() == "customer"
    assert payload["type"] == "access"
    assert payload["exp"]


def test_refresh_token_creation():
    test_token = TokenService.create_refresh_token(email="user@example.com", user_id=1, role="customer")[0]
    assert test_token

    payload = jwt.decode(test_token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "user@example.com"
    assert payload["id"] == 1
    assert payload["role"].lower() == "customer"
    assert payload["jti"]
    assert payload["type"] == "refresh"
    assert payload["exp"]



def test_token_expiration():
    access_token = TokenService.create_access_token(
        email="user@example.com",
        user_id=1,
        role="customer",
        expires_delta=timedelta(seconds=1)
    )

    sleep(2)  # ensure expiration

    with pytest.raises(JWTError):
        jwt.decode(
            access_token,
            key=settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
