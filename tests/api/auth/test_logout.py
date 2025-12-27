from models.users import User
from utils.hashing import get_password_hash


async def test_logout_success(client, verified_user, session):
    """Test successful logout with valid refresh token."""
    # Login to get tokens
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    
    assert response.status_code == 200
    refresh_token = response.json()["refresh_token"]
    
    # Logout
    response = await client.post("/auth/logout", json={
        "refresh_token": refresh_token
    })
    
    assert response.status_code == 200
    assert "logged out" in response.json()["message"].lower()
    
    # Verify token is revoked - try to use it
    response = await client.post("/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    # Should fail because token is revoked
    assert response.status_code == 401


async def test_logout_without_token(client):
    """Test that logout without token fails validation."""
    # Missing refresh_token field
    response = await client.post("/auth/logout", json={})
    
    # Pydantic validation error
    assert response.status_code == 422


async def test_logout_with_empty_token(client):
    """Test that logout with empty token fails validation."""
    # Empty string should fail schema validation
    response = await client.post("/auth/logout", json={
        "refresh_token": ""
    })
    
    # Pydantic validation error
    assert response.status_code == 422


async def test_logout_with_invalid_token(client):
    """Test logout with malformed/invalid token."""
    # Invalid token format
    response = await client.post("/auth/logout", json={
        "refresh_token": "invalid_token_format"
    })
    
    # Implementation silently handles invalid tokens (returns success)
    # This is acceptable behavior - idempotent logout
    assert response.status_code == 200


async def test_logout_with_already_revoked_token(client, verified_user, session):
    """Test that logging out with already revoked token succeeds (idempotent)."""
    # Login to get tokens
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    
    refresh_token = response.json()["refresh_token"]
    
    # Logout once
    response = await client.post("/auth/logout", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    
    # Logout again with same token (already revoked)
    response = await client.post("/auth/logout", json={
        "refresh_token": refresh_token
    })
    
    # Should still succeed (idempotent operation)
    assert response.status_code == 200


async def test_logout_does_not_affect_other_tokens(client, verified_user, session):
    """Test that logging out one token doesn't revoke other tokens for the same user."""
    # Login twice to get two different token pairs
    response1 = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    token1 = response1.json()["refresh_token"]
    
    response2 = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    token2 = response2.json()["refresh_token"]
    
    # Logout with first token
    response = await client.post("/auth/logout", json={
        "refresh_token": token1
    })
    assert response.status_code == 200
    
    # Second token should still work
    response = await client.post("/auth/refresh", json={
        "refresh_token": token2
    })
    
    # Should succeed
    assert response.status_code == 200
