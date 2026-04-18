import pytest
from fastapi import BackgroundTasks, HTTPException
from services.users import UserService


async def _setup_pending_change(session, user):
    """Helper: put user into pending password change state. Returns the RAW token."""
    from unittest.mock import patch
    import secrets as _secrets
    raw_token = _secrets.token_urlsafe(32)
    with patch("services.users.secrets.token_urlsafe", return_value=raw_token):
        bg = BackgroundTasks()
        await UserService.request_password_change(session, user, "TestPassword123!", "NewPass123!", bg)
    return raw_token


async def test_deny_password_change_clears_fields(session, verified_user):
    """Clears all pending password change fields and revokes tokens."""
    raw_token = await _setup_pending_change(session, verified_user)

    bg = BackgroundTasks()
    await UserService.deny_password_change(session, raw_token, bg)

    await session.refresh(verified_user)
    assert verified_user.pending_password_hash is None
    assert verified_user.password_change_token is None
    assert verified_user.password_change_expires_at is None


async def test_deny_password_change_invalid_token(session, verified_user):
    """Raises 400 for an unknown token."""
    bg = BackgroundTasks()
    with pytest.raises(HTTPException) as exc:
        await UserService.deny_password_change(session, "invalidtoken", bg)
    assert exc.value.status_code == 400
