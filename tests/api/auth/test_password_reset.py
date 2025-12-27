from models.users import User
from utils.hashing import get_password_hash, verify_password
from datetime import datetime, timedelta, UTC, timezone
import secrets


async def test_forgot_password_success(client, verified_user, session):
    """Test successful password reset request."""
    response = await client.post("/auth/forgot-password", json={
        "email": verified_user.email
    })
    
    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["message"].lower()
    
    # Verify reset token was stored in database
    session.refresh(verified_user)
    assert verified_user.password_reset_token is not None
    assert verified_user.password_reset_expires_at is not None
    assert verified_user.password_reset_expires_at.replace(tzinfo=timezone.utc) > datetime.now(UTC)


async def test_forgot_password_nonexistent_user(client):
    """Test password reset for non-existent email (doesn't leak user existence)."""
    response = await client.post("/auth/forgot-password", json={
        "email": "nonexistent@example.com"
    })
    
    # Should return same message (don't leak user existence)
    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["message"].lower()


async def test_reset_password_success(client, verified_user, session):
    """Test successful password reset with valid token."""
    # Request password reset
    response = await client.post("/auth/forgot-password", json={
        "email": verified_user.email
    })
    assert response.status_code == 200
    
    # Get reset token from database
    session.refresh(verified_user)
    reset_token = verified_user.password_reset_token
    
    # Reset password
    new_password = "NewSecurePass123!"
    response = await client.post("/auth/reset-password", json={
        "token": reset_token,
        "new_password": new_password
    })
    
    assert response.status_code == 200
    assert "password updated" in response.json()["message"].lower()
    
    # Verify password was changed
    session.refresh(verified_user)
    assert verify_password(new_password, verified_user.hashed_password)
    
    # Verify reset token was cleared
    assert verified_user.password_reset_token is None
    assert verified_user.password_reset_expires_at is None
    
    # Verify can login with new password
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": new_password
    })
    assert response.status_code == 200


async def test_reset_password_invalid_token(client):
    """Test password reset with invalid token fails."""
    response = await client.post("/auth/reset-password", json={
        "token": "invalid_token_12345",
        "new_password": "NewPassword123!"
    })
    
    assert response.status_code == 400
    assert "invalid or expired" in response.json()["detail"].lower()


async def test_reset_password_expired_token(client, verified_user, session):
    """Test password reset with expired token fails."""
    # Manually create expired reset token
    reset_token = secrets.token_urlsafe(32)
    verified_user.password_reset_token = reset_token
    verified_user.password_reset_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    session.commit()
    
    # Attempt reset with expired token
    response = await client.post("/auth/reset-password", json={
        "token": reset_token,
        "new_password": "NewPassword123!"
    })
    
    assert response.status_code == 400
    assert "invalid or expired" in response.json()["detail"].lower()


async def test_reset_password_weak_password(client, verified_user, session):
    """Test password reset with weak password fails validation."""
    # Request password reset
    await client.post("/auth/forgot-password", json={
        "email": verified_user.email
    })
    
    session.refresh(verified_user)
    reset_token = verified_user.password_reset_token
    
    # Try to reset with weak password
    response = await client.post("/auth/reset-password", json={
        "token": reset_token,
        "new_password": "weak"  # Too short, no numbers
    })
    
    # Pydantic validation error
    assert response.status_code == 422


async def test_reset_password_revokes_all_tokens(client, verified_user, session):
    """Test that password reset revokes all existing refresh tokens."""
    # Login to get tokens
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    old_refresh_token = response.json()["refresh_token"]
    
    # Request password reset
    await client.post("/auth/forgot-password", json={
        "email": verified_user.email
    })
    
    session.refresh(verified_user)
    reset_token = verified_user.password_reset_token
    
    # Reset password
    response = await client.post("/auth/reset-password", json={
        "token": reset_token,
        "new_password": "NewSecurePass123!"
    })
    assert response.status_code == 200
    
    # Try to use old refresh token (should be revoked)
    response = await client.post("/auth/refresh", json={
        "refresh_token": old_refresh_token
    })
    
    # Should fail because all tokens were revoked
    assert response.status_code == 401


async def test_reset_password_token_single_use(client, verified_user, session):
    """Test that reset token can only be used once."""
    # Request password reset
    await client.post("/auth/forgot-password", json={
        "email": verified_user.email
    })
    
    session.refresh(verified_user)
    reset_token = verified_user.password_reset_token
    
    # Use token once
    response = await client.post("/auth/reset-password", json={
        "token": reset_token,
        "new_password": "NewPassword123!"
    })
    assert response.status_code == 200
    
    # Try to use same token again
    response = await client.post("/auth/reset-password", json={
        "token": reset_token,
        "new_password": "AnotherPassword123!"
    })
    
    # Should fail (token was cleared after first use)
    assert response.status_code == 400
    assert "invalid or expired" in response.json()["detail"].lower()
