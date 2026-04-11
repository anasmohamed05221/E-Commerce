import pytest
from datetime import datetime, timezone, timedelta
from fastapi import BackgroundTasks, HTTPException
from services.users import UserService
from utils.hashing import verify_password


def _setup_pending_change(session, user):
    """Helper: put user into pending password change state."""
    bg = BackgroundTasks()
    UserService.request_password_change(session, user, "TestPassword123!", "NewPass123!", bg)
    session.refresh(user)
    return user.password_change_token


def test_confirm_password_change_applies_new_password(session, verified_user):
    """Applies pending hash, clears all pending fields."""
    token = _setup_pending_change(session, verified_user)

    UserService.confirm_password_change(session, token)

    session.refresh(verified_user)
    assert verify_password("NewPass123!", verified_user.hashed_password)
    assert verified_user.pending_password_hash is None
    assert verified_user.password_change_token is None
    assert verified_user.password_change_expires_at is None


def test_confirm_password_change_invalid_token(session, verified_user):
    """Raises 400 for an unknown token."""
    with pytest.raises(HTTPException) as exc:
        UserService.confirm_password_change(session, "invalidtoken")
    assert exc.value.status_code == 400


def test_confirm_password_change_expired_token(session, verified_user):
    """Raises 400 when token exists but is expired."""
    _setup_pending_change(session, verified_user)
    verified_user.password_change_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    session.commit()

    with pytest.raises(HTTPException) as exc:
        UserService.confirm_password_change(session, verified_user.password_change_token)
    assert exc.value.status_code == 400


def test_confirm_password_change_null_pending_hash(session, verified_user):
    """Raises 400 when token is valid but pending_password_hash is None."""
    _setup_pending_change(session, verified_user)
    token = verified_user.password_change_token
    verified_user.pending_password_hash = None
    session.commit()

    with pytest.raises(HTTPException) as exc:
        UserService.confirm_password_change(session, token)
    assert exc.value.status_code == 400
