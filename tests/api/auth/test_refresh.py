from models.users import User
from models.refresh_tokens import RefreshToken
from utils.hashing import get_password_hash
from services.token import TokenService
from datetime import datetime, timedelta, UTC
from jose import jwt
from core.config import settings
import hashlib


async def test_refresh_token_success(client, verified_user, session):
    """Test successful token refresh with valid refresh token."""
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })

    assert response.status_code == 200
    old_tokens = response.json()
    old_refresh_token = old_tokens["refresh_token"]

    response = await client.post("/auth/refresh", json={
        "refresh_token": old_refresh_token
    })

    assert response.status_code == 200
    new_tokens = response.json()

    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["token_type"] == "bearer"

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
    response = await client.post("/auth/token", data={
        "username": verified_user.email,
        "password": "TestPassword123!"
    })

    old_refresh_token = response.json()["refresh_token"]

    response = await client.post("/auth/refresh", json={
        "refresh_token": old_refresh_token
    })

    assert response.status_code == 200

    response = await client.post("/auth/refresh", json={
        "refresh_token": old_refresh_token
    })

    assert response.status_code == 401
    assert "revoked" in response.json()["detail"].lower() or "not found" in response.json()["detail"].lower()


async def test_refresh_expired_token(client, session, test_tenant):
    """Test that expired refresh tokens cannot be used."""
    user = User(
        tenant_id=test_tenant.id,
        email="expired_refresh@example.com",
        first_name="Expired",
        last_name="Refresh",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111111",
        is_verified=True,
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    refresh_token, jti, _ = TokenService.create_refresh_token(
        str(test_tenant.id), user.email, user.id, user.role
    )

    token_hash = hashlib.sha256(jti.encode()).hexdigest()
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) - timedelta(seconds=1)
    )
    session.add(db_token)
    await session.commit()

    response = await client.post("/auth/refresh", json={
        "refresh_token": refresh_token
    })

    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


async def test_refresh_revoked_token(client, session, test_tenant):
    """Test that revoked refresh tokens cannot be used."""
    user = User(
        tenant_id=test_tenant.id,
        email="revoked_refresh@example.com",
        first_name="Revoked",
        last_name="Refresh",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111111",
        is_verified=True,
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    tokens = await TokenService.create_tokens(str(test_tenant.id), user.email, user.id, user.role, session)

    await TokenService.revoke_token(tokens["refresh_token"], session)

    response = await client.post("/auth/refresh", json={
        "refresh_token": tokens["refresh_token"]
    })

    assert response.status_code == 401
    assert "revoked" in response.json()["detail"].lower() or "not found" in response.json()["detail"].lower()


async def test_refresh_invalid_token_format(client):
    """Test that malformed/invalid refresh tokens are rejected."""
    response = await client.post("/auth/refresh", json={
        "refresh_token": "invalid_token_format"
    })

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


async def test_refresh_empty_token(client):
    """Test that empty refresh token is rejected."""
    response = await client.post("/auth/refresh", json={
        "refresh_token": ""
    })

    assert response.status_code == 422


async def test_refresh_missing_token(client):
    """Test that missing refresh token field is rejected."""
    response = await client.post("/auth/refresh", json={})

    assert response.status_code == 422


async def test_refresh_token_wrong_type(client, test_tenant):
    """Test that an access token cannot be used as a refresh token."""
    access_token = TokenService.create_access_token(
        str(test_tenant.id), "test@example.com", 1, "customer"
    )

    response = await client.post("/auth/refresh", json={
        "refresh_token": access_token
    })

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower() or "type" in response.json()["detail"].lower()
