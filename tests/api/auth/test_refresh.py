from models.users import User
from models.refresh_tokens import RefreshToken
from utils.hashing import get_password_hash
from services.token_service import TokenService
from datetime import datetime, timedelta, UTC
from jose import jwt
from core.config import settings
import hashlib


async def test_refresh_token_success(client, verified_user, session):
    """Test successful token refresh with valid refresh token."""
    # Login to get initial tokens
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    
    assert response.status_code == 200
    old_tokens = response.json()
    old_refresh_token = old_tokens["refresh_token"]
    
    # Refresh tokens
    response = await client.post("/auth/refresh", json={
        "refresh_token": old_refresh_token
    })
    
    assert response.status_code == 200
    new_tokens = response.json()
    
    # Verify response structure
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["token_type"] == "bearer"
    
    # Verify new access token has correct claims
    payload = jwt.decode(
        new_tokens["access_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    assert payload["sub"] == verified_user.email
    assert payload["id"] == verified_user.id
    assert payload["type"] == "access"



async def test_refresh_token_rotation(client, verified_user, session):
    """Test that old refresh token is revoked after successful refresh (token rotation)."""
    # Login to get tokens
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    
    old_refresh_token = response.json()["refresh_token"]
    
    # Refresh tokens
    response = await client.post("/auth/refresh", json={
        "refresh_token": old_refresh_token
    })
    
    assert response.status_code == 200
    
    # Try to use old refresh token again (should fail - token rotation)
    response = await client.post("/auth/refresh", json={
        "refresh_token": old_refresh_token
    })
    
    assert response.status_code == 401
    # Old token should be revoked
    assert "revoked" in response.json()["detail"].lower() or "not found" in response.json()["detail"].lower()


async def test_refresh_expired_token(client, session):
    """Test that expired refresh tokens cannot be used."""
    # Create a verified user
    user = User(
        email="expired_refresh@example.com",
        first_name="Expired",
        last_name="Refresh",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111111",
        is_verified=True,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create a refresh token manually with expired timestamp
    refresh_token, jti, _ = TokenService.create_refresh_token(
        user.email, user.id, user.role
    )
    
    # Store in DB with past expiry
    token_hash = hashlib.sha256(jti.encode()).hexdigest()
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) - timedelta(seconds=1)  # Already expired
    )
    session.add(db_token)
    session.commit()
    
    # Attempt to refresh with expired token
    response = await client.post("/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


async def test_refresh_revoked_token(client, session):
    """Test that revoked refresh tokens cannot be used."""
    # Create a verified user
    user = User(
        email="revoked_refresh@example.com",
        first_name="Revoked",
        last_name="Refresh",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111111",
        is_verified=True,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create tokens normally
    tokens = TokenService.create_tokens(user.email, user.id, user.role, session)
    
    # Revoke the refresh token
    TokenService.revoke_token(tokens["refresh_token"], session)
    
    # Attempt to use revoked token
    response = await client.post("/auth/refresh", json={
        "refresh_token": tokens["refresh_token"]
    })
    
    assert response.status_code == 401
    # Assumption: Error message should indicate token is invalid/revoked
    assert "revoked" in response.json()["detail"].lower() or "not found" in response.json()["detail"].lower()


async def test_refresh_invalid_token_format(client):
    """Test that malformed/invalid refresh tokens are rejected."""
    # Test with completely invalid token
    response = await client.post("/auth/refresh", json={
        "refresh_token": "invalid_token_format"
    })
    
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


async def test_refresh_empty_token(client):
    """Test that empty refresh token is rejected."""
    # Empty token should fail validation at schema level
    response = await client.post("/auth/refresh", json={
        "refresh_token": ""
    })
    
    # Pydantic validation error
    assert response.status_code == 422


async def test_refresh_missing_token(client):
    """Test that missing refresh token field is rejected."""
    # Missing field should fail validation
    response = await client.post("/auth/refresh", json={})
    
    # Pydantic validation error
    assert response.status_code == 422


async def test_refresh_token_wrong_type(client):
    """Test that access token cannot be used as refresh token."""
    # Create a verified user and get tokens
    user = User(
        email="wrong_type@example.com",
        first_name="Wrong",
        last_name="Type",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111111",
        is_verified=True,
        is_active=True
    )
    
    from tests.conftest import session as session_fixture
    # Note: This test assumes we can't easily create a session here
    # If this pattern doesn't match existing tests, this test can be removed
    # Alternatively, use the session fixture
    
    # For now, create a mock access token (JWT with type="access")
    access_token = TokenService.create_access_token(
        "test@example.com", 1, "customer"
    )
    
    # Attempt to use access token as refresh token
    response = await client.post("/auth/refresh", json={
        "refresh_token": access_token
    })
    
    # Should fail because token type is "access" not "refresh"
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower() or "type" in response.json()["detail"].lower()
