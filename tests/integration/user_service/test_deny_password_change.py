import pytest
from fastapi import BackgroundTasks, HTTPException
from services.users import UserService


def _setup_pending_change(session, user):
    """Helper: put user into pending password change state."""
    bg = BackgroundTasks()
    UserService.request_password_change(session, user, "TestPassword123!", "NewPass123!", bg)
    session.refresh(user)
    return user.password_change_token


def test_deny_password_change_clears_fields(session, verified_user):
    """Clears all pending password change fields and revokes tokens."""
    _setup_pending_change(session, verified_user)
    token = verified_user.password_change_token

    bg = BackgroundTasks()
    UserService.deny_password_change(session, token, bg)

    session.refresh(verified_user)
    assert verified_user.pending_password_hash is None
    assert verified_user.password_change_token is None
    assert verified_user.password_change_expires_at is None


def test_deny_password_change_invalid_token(session, verified_user):
    """Raises 400 for an unknown token."""
    bg = BackgroundTasks()
    with pytest.raises(HTTPException) as exc:
        UserService.deny_password_change(session, "invalidtoken", bg)
    assert exc.value.status_code == 400
