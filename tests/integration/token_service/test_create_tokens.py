import pytest
from sqlalchemy import select
from services.token import TokenService
from models.refresh_tokens import RefreshToken
from jose import jwt
from core.config import settings
import hashlib


async def test_create_refresh_token(session, test_user):
    """Test that create_tokens stores refresh token in DB."""
    tokens = await TokenService.create_tokens(test_user.email, test_user.id, test_user.role, session)

    # Verify response structure
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # Verify refresh token is a non-empty string
    assert isinstance(tokens["refresh_token"], str)
    assert len(tokens["refresh_token"]) > 0

    payload = jwt.decode(
        tokens["refresh_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    jti = payload["jti"]

    # Verify token hash is in database
    token_hash = hashlib.sha256(jti.encode()).hexdigest()

    db_token = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    assert db_token is not None
    assert db_token.user_id == test_user.id
    assert db_token.revoked is False


async def test_refresh_token_rotation(session, test_user):
    """Test that refreshing revokes old token and creates new one."""
    # Create initial tokens
    old_tokens = await TokenService.create_tokens(test_user.email, test_user.id, test_user.role, session)

    # Refresh
    new_tokens = await TokenService.refresh_access_token(old_tokens["refresh_token"], session)

    # Verify old refresh token is revoked
    old_payload = jwt.decode(old_tokens["refresh_token"], key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    old_jti = old_payload["jti"]
    old_hash = hashlib.sha256(old_jti.encode()).hexdigest()

    old_db_token = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == old_hash))

    assert old_db_token.revoked is True

    # Verify new token is different
    assert new_tokens["refresh_token"] != old_tokens["refresh_token"]

    # Verify new refresh token is stored in db
    new_payload = jwt.decode(new_tokens["refresh_token"], key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    new_jti = new_payload["jti"]
    new_hash = hashlib.sha256(new_jti.encode()).hexdigest()

    new_db_token = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == new_hash))

    assert new_db_token is not None
    assert new_db_token.user_id == test_user.id
    assert new_db_token.revoked is False
