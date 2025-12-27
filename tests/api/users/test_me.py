from jose import jwt
from core.config import settings
from datetime import datetime, timedelta, UTC


async def test_get_me_success(client, verified_user, session):
    """Test getting current user info with valid token."""
    # Login to get access token
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    
    access_token = response.json()["access_token"]
    
    # Get user info
    response = await client.get("/users/me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response contains correct user data
    assert data["id"] == verified_user.id
    assert data["email"] == verified_user.email
    assert data["first_name"] == verified_user.first_name
    assert data["last_name"] == verified_user.last_name
    assert data["phone_number"] == verified_user.phone_number
    
    # Verify sensitive data is NOT included
    assert "hashed_password" not in data
    assert "password" not in data
    assert "password_reset_token" not in data


async def test_get_me_no_token(client):
    """Test that accessing /users/me without token returns 401."""
    response = await client.get("/users/me")
    
    assert response.status_code == 401
    assert "not authenticated" in response.json()["detail"].lower()


async def test_get_me_invalid_token(client):
    """Test that accessing /users/me with invalid token returns 401."""
    response = await client.get("/users/me", headers={
        "Authorization": "Bearer invalid_token_format"
    })
    
    assert response.status_code == 401
    assert "could not validate" in response.json()["detail"].lower()


async def test_get_me_expired_token(client, verified_user):
    """Test that accessing /users/me with expired token returns 401."""
    # Create an expired access token manually
    expired_payload = {
        "sub": verified_user.email,
        "id": verified_user.id,
        "role": verified_user.role,
        "type": "access",
        "exp": datetime.now(UTC) - timedelta(minutes=1)  # Expired 1 minute ago
    }
    
    expired_token = jwt.encode(
        expired_payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    response = await client.get("/users/me", headers={
        "Authorization": f"Bearer {expired_token}"
    })
    
    assert response.status_code == 401


async def test_get_me_wrong_token_type(client, verified_user, session):
    """Test that using refresh token instead of access token fails."""
    # Login to get tokens
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    
    refresh_token = response.json()["refresh_token"]
    
    # Try to use refresh token for protected endpoint
    response = await client.get("/users/me", headers={
        "Authorization": f"Bearer {refresh_token}"
    })
    
    assert response.status_code == 401
    # Should fail because token type is "refresh" not "access"
    assert "invalid token type" in response.json()["detail"].lower() or "access token required" in response.json()["detail"].lower()


async def test_get_me_malformed_authorization_header(client):
    """Test that malformed Authorization header is rejected."""
    # Missing "Bearer" prefix
    response = await client.get("/users/me", headers={
        "Authorization": "some_token"
    })
    
    assert response.status_code == 401
