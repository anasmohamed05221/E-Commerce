from models.refresh_tokens import RefreshToken


async def test_deactivate_user_success(client, verified_user, session):
    """Test successful account deactivation."""
    # Login to get access token
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    
    access_token = response.json()["access_token"]
    refresh_token = response.json()["refresh_token"]
    
    # Deactivate account
    response = await client.request("DELETE", "/users/deactivate",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"password": "TestPassword123!"}
    )
    
    assert response.status_code == 200
    assert "deactivated" in response.json()["message"].lower()
    
    # Verify user is deactivated in database
    session.refresh(verified_user)
    assert verified_user.is_active is False
    
    # Verify all refresh tokens are revoked
    tokens = session.query(RefreshToken).filter(
        RefreshToken.user_id == verified_user.id
    ).all()
    
    for token in tokens:
        assert token.revoked is True
    
    # Verify cannot login with deactivated account
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    
    assert response.status_code == 401


async def test_deactivate_user_unauthenticated(client):
    """Test that deactivation requires authentication."""
    response = await client.request("DELETE", "/users/deactivate",
        json={"password": "TestPassword123!"}
    )
    
    assert response.status_code == 401


async def test_deactivate_user_invalid_token(client):
    """Test that deactivation fails with invalid token."""
    response = await client.request("DELETE", "/users/deactivate",
        headers={"Authorization": "Bearer invalid_token"},
        json={"password": "TestPassword123!"}
    )
    
    assert response.status_code == 401


async def test_deactivate_user_wrong_password(client, verified_user, session):
    """Test that deactivation fails with incorrect password."""
    # Login to get access token
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    
    access_token = response.json()["access_token"]
    
    # Try to deactivate with wrong password
    response = await client.request("DELETE", "/users/deactivate",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"password": "WrongPassword123!"}
    )
    
    assert response.status_code == 401
    assert "incorrect password" in response.json()["detail"].lower()
    
    # Verify user is still active
    session.refresh(verified_user)
    assert verified_user.is_active is True


async def test_deactivate_user_missing_password(client, verified_user):
    """Test that deactivation fails without password."""
    # Login to get access token
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    
    access_token = response.json()["access_token"]
    
    # Try to deactivate without password
    response = await client.request("DELETE", "/users/deactivate",
        headers={"Authorization": f"Bearer {access_token}"},
        json={}
    )
    
    # Pydantic validation error
    assert response.status_code == 422


async def test_deactivate_user_revokes_all_sessions(client, verified_user, session):
    """Test that deactivation revokes all user sessions."""
    # Login twice to create multiple sessions
    response1 = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    token1 = response1.json()["access_token"]
    refresh1 = response1.json()["refresh_token"]
    
    response2 = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })
    refresh2 = response2.json()["refresh_token"]
    
    # Deactivate using first session
    response = await client.request("DELETE", "/users/deactivate",
        headers={"Authorization": f"Bearer {token1}"},
        json={"password": "TestPassword123!"}
    )
    
    assert response.status_code == 200
    
    # Verify both refresh tokens are revoked
    response = await client.post("/auth/refresh", json={
        "refresh_token": refresh1
    })
    assert response.status_code == 401
    
    response = await client.post("/auth/refresh", json={
        "refresh_token": refresh2
    })
    assert response.status_code == 401

