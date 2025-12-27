import pytest
from services.token_service import TokenService
from models.users import User
from models.refresh_tokens import RefreshToken
from utils.hashing import get_password_hash
from jose import jwt
from core.config import settings
import hashlib
from fastapi import HTTPException
from datetime import datetime, timedelta, UTC

def create_test_user(session):
    """Helper to create a verified user for token tests."""

    user = User(
        email="token_test@example.com",
        first_name="Token",
        last_name="Test",
        hashed_password=get_password_hash("password123"),
        phone_number="+201111111111",
        is_verified=True,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user



def test_create_refresh_token(session):
    """Test that create_tokens stores refresh token in DB."""

    user = create_test_user(session)
    tokens = TokenService.create_tokens(user.email, user.id, user.role, session)

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

    db_token = session.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    assert db_token is not None
    assert db_token.user_id == user.id
    assert db_token.revoked is False



def test_refresh_token_rotation(session):
    """Test that refreshing revokes old token and creates new one."""
    user = create_test_user(session)

    # Create initial tokens
    old_tokens = TokenService.create_tokens(user.email, user.id, user.role, session)

    # Refresh
    new_tokens = TokenService.refresh_access_token(old_tokens["refresh_token"], session)

    # Verify old refresh token is revoked
    old_payload = jwt.decode(old_tokens["refresh_token"], key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    old_jti = old_payload["jti"]
    old_hash = hashlib.sha256(old_jti.encode()).hexdigest()

    old_db_token = session.query(RefreshToken).filter(RefreshToken.token_hash == old_hash).first()

    assert old_db_token.revoked is True

    # Verify new token is different
    assert new_tokens["refresh_token"] != old_tokens["refresh_token"]


    # Verify new refresh token is stored in db
    new_payload = jwt.decode(new_tokens["refresh_token"], key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    new_jti = new_payload["jti"]
    new_hash = hashlib.sha256(new_jti.encode()).hexdigest()

    new_db_token = session.query(RefreshToken).filter(RefreshToken.token_hash == new_hash).first()

    assert new_db_token is not None
    assert new_db_token.user_id == user.id
    assert new_db_token.revoked is False


def test_revoke_token(session):
    """Test revoking a single refresh token."""
    user = create_test_user(session)
    tokens = TokenService.create_tokens(user.email, user.id, user.role, session)

    # Revoke
    TokenService.revoke_token(tokens["refresh_token"], session)

    # Verify it's revoked
    payload = jwt.decode(tokens["refresh_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    jti = payload["jti"]
    token_hash = hashlib.sha256(jti.encode()).hexdigest()
    
    db_token = session.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()
    
    assert db_token.revoked is True



def test_revoke_all_tokens(session):
    """Test revoking all tokens for a user."""
    user = create_test_user(session)
    
    # Create multiple tokens
    tokens1 = TokenService.create_tokens(user.email, user.id, user.role, session)
    tokens2 = TokenService.create_tokens(user.email, user.id, user.role, session)
    
    # Revoke all
    TokenService.revoke_all_user_tokens(user.id, session)
    
    # Verify all are revoked
    user_tokens = session.query(RefreshToken).filter(
        RefreshToken.user_id == user.id
    ).all()
    
    assert all(t.revoked for t in user_tokens)



def test_revoked_token_fails_refresh(session):
    """Test that revoked tokens cannot be refreshed."""
    user = create_test_user(session)
    tokens = TokenService.create_tokens(user.email, user.id, user.role, session)
    
    # Revoke
    TokenService.revoke_token(tokens["refresh_token"], session)
    
    # Try to refresh
    with pytest.raises(HTTPException) as exc_info:
        TokenService.refresh_access_token(tokens["refresh_token"], session)
    
    assert exc_info.value.status_code == 401



def test_expired_token_fails_refresh(session):
    """Test that expired tokens cannot be refreshed."""
    user = create_test_user(session)
    
    # Create token with 1-second expiry
    short_token, jti, expires_at = TokenService.create_refresh_token(
        user.email, user.id, user.role
    )
    # Manually create DB entry with past expiry
    token_hash = hashlib.sha256(jti.encode()).hexdigest()
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) - timedelta(seconds=1)  # Already expired
    )
    session.add(db_token)
    session.commit()
    
    # Try to refresh
    with pytest.raises(HTTPException) as exc_info:
        TokenService.refresh_access_token(short_token, session)
    
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()