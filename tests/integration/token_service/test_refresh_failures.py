import pytest
from services.token import TokenService
from models.refresh_tokens import RefreshToken
from fastapi import HTTPException
from datetime import datetime, timedelta, UTC
import hashlib


async def test_revoked_token_fails_refresh(session, test_user):
    """Test that revoked tokens cannot be refreshed."""
    tokens = await TokenService.create_tokens(test_user.email, test_user.id, test_user.role, session)

    # Revoke
    await TokenService.revoke_token(tokens["refresh_token"], session)

    # Try to refresh
    with pytest.raises(HTTPException) as exc_info:
        await TokenService.refresh_access_token(tokens["refresh_token"], session)

    assert exc_info.value.status_code == 401


async def test_expired_token_fails_refresh(session, test_user):
    """Test that expired tokens cannot be refreshed."""
    # Create token with 1-second expiry
    short_token, jti, expires_at = TokenService.create_refresh_token(
        test_user.email, test_user.id, test_user.role
    )
    # Manually create DB entry with past expiry
    token_hash = hashlib.sha256(jti.encode()).hexdigest()
    db_token = RefreshToken(
        user_id=test_user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) - timedelta(seconds=1)  # Already expired
    )
    session.add(db_token)
    await session.commit()

    # Try to refresh
    with pytest.raises(HTTPException) as exc_info:
        await TokenService.refresh_access_token(short_token, session)

    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()
