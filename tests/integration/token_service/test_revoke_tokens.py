import pytest
from sqlalchemy import select
from services.token import TokenService
from models.refresh_tokens import RefreshToken
from jose import jwt
from core.config import settings
import hashlib


async def test_revoke_token(session, test_user):
    """Test revoking a single refresh token."""
    tokens = await TokenService.create_tokens(test_user.email, test_user.id, test_user.role, session)

    # Revoke
    await TokenService.revoke_token(tokens["refresh_token"], session)

    # Verify it's revoked
    payload = jwt.decode(tokens["refresh_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    jti = payload["jti"]
    token_hash = hashlib.sha256(jti.encode()).hexdigest()

    db_token = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    assert db_token.revoked is True


async def test_revoke_all_tokens(session, test_user):
    """Test revoking all tokens for a user."""
    # Create multiple tokens
    await TokenService.create_tokens(test_user.email, test_user.id, test_user.role, session)
    await TokenService.create_tokens(test_user.email, test_user.id, test_user.role, session)

    # Revoke all
    await TokenService.revoke_all_user_tokens(test_user.id, session)

    # Verify all are revoked
    user_tokens = (await session.scalars(
        select(RefreshToken).where(RefreshToken.user_id == test_user.id)
    )).all()

    assert all(t.revoked for t in user_tokens)
