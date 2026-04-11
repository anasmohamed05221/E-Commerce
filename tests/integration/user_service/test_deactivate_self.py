import pytest
from fastapi import HTTPException
from services.users import UserService
from models.refresh_tokens import RefreshToken
from services.token import TokenService


def test_deactivate_self_wrong_password(session, verified_user):
    """Raises 401 when password is incorrect."""
    with pytest.raises(HTTPException) as exc:
        UserService.deactivate_self(session, verified_user, "wrongpassword")
    assert exc.value.status_code == 401


def test_deactivate_self_sets_inactive(session, verified_user):
    """Sets is_active=False on success."""
    UserService.deactivate_self(session, verified_user, "TestPassword123!")

    session.refresh(verified_user)
    assert verified_user.is_active is False


def test_deactivate_self_revokes_tokens(session, verified_user):
    """Revokes all refresh tokens on success."""
    TokenService.create_tokens(verified_user.email, verified_user.id, verified_user.role, session)

    UserService.deactivate_self(session, verified_user, "TestPassword123!")

    active_tokens = session.query(RefreshToken).filter(
        RefreshToken.user_id == verified_user.id,
        RefreshToken.revoked == False  # noqa: E712
    ).count()
    assert active_tokens == 0
