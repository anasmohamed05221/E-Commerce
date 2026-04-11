import pytest
from fastapi import BackgroundTasks, HTTPException
from services.users import UserService


def test_request_password_change_wrong_password(session, verified_user):
    """Raises 401 when current password is incorrect."""
    bg = BackgroundTasks()
    with pytest.raises(HTTPException) as exc:
        UserService.request_password_change(session, verified_user, "wrongpassword", "NewPass123!", bg)
    assert exc.value.status_code == 401


def test_request_password_change_stores_pending_data(session, verified_user):
    """Stores pending hash and token in DB on valid request."""
    bg = BackgroundTasks()
    UserService.request_password_change(session, verified_user, "TestPassword123!", "NewPass123!", bg)

    session.refresh(verified_user)
    assert verified_user.pending_password_hash is not None
    assert verified_user.password_change_token is not None
    assert verified_user.password_change_expires_at is not None