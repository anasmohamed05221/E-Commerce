import pytest
from services.token import TokenService
from models.refresh_tokens import RefreshToken
from jose import jwt
from core.config import settings
import hashlib


def test_revoke_token(session, test_user):
    """Test revoking a single refresh token."""
    tokens = TokenService.create_tokens(test_user.email, test_user.id, test_user.role, session)

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


def test_revoke_all_tokens(session, test_user):
    """Test revoking all tokens for a user."""
    # Create multiple tokens
    tokens1 = TokenService.create_tokens(test_user.email, test_user.id, test_user.role, session)
    tokens2 = TokenService.create_tokens(test_user.email, test_user.id, test_user.role, session)

    # Revoke all
    TokenService.revoke_all_user_tokens(test_user.id, session)

    # Verify all are revoked
    user_tokens = session.query(RefreshToken).filter(
        RefreshToken.user_id == test_user.id
    ).all()

    assert all(t.revoked for t in user_tokens)
