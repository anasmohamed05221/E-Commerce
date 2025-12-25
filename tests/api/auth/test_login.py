from tests.conftest import session, client, verified_user
from models.users import User
from utils.hashing import get_password_hash
import pytest
from jose import jwt
from core.config import settings


async def test_login_success(client, verified_user):
    """Test successfull user login."""

    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })

    assert response.status_code == 200

    # Verify response contains tokens
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

    # Verify token structure
    data = response.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    
    assert isinstance(access_token, str)
    assert len(access_token) > 0 

    assert isinstance(refresh_token, str)
    assert len(refresh_token) > 0 
    
    assert data["token_type"] == "bearer"

    # Verify token claims
    payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    assert payload["sub"] == verified_user.email
    assert payload["id"] == verified_user.id
    assert payload["role"] == verified_user.role
    assert payload["type"] == "access"


async def test_login_wrong_password(client, verified_user):
    """Test login with incorrect password."""

    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "WrongPassword123!"
    })

    assert response.status_code == 401
    assert "could not validate user" in response.json()["detail"].lower()


async def test_login_nonexistent_user(client):
    """Test login with non-existent email."""
    response = await client.post("/auth/token", data={
        "username": "nonexistent@example.com",
        "password": "Password123!"
    })
    
    assert response.status_code == 401


async def test_login_unverified_email(client, session):
    """Test login with unverified email."""
    
    unverified_user = User(
        email="unverified@example.com",
        first_name="Unverified",
        last_name="User",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111111",
        is_verified=False,
        is_active=True
    )
    session.add(unverified_user)
    session.commit()
    
    response = await client.post("/auth/token", data={
        "username": "unverified@example.com",
        "password": "TestPassword123!"
    })
    
    assert response.status_code == 403
    assert "not verified" in response.json()["detail"].lower()


async def test_login_inactive_user(client, session):
    """Test login for an inactive user"""
    inactive_user = User(
        email="inactive@example.com",
        first_name="Inactive",
        last_name="User",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111111",
        is_verified=True,
        is_active=False
    )
    session.add(inactive_user)
    session.commit()
    
    response = await client.post("/auth/token", data={
        "username": "inactive@example.com",
        "password": "TestPassword123!"
    })
    
    assert response.status_code == 401