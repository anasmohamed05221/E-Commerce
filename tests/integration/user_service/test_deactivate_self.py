import pytest
from sqlalchemy import select, func
from fastapi import HTTPException
from services.users import UserService
from models.refresh_tokens import RefreshToken
from services.token import TokenService


async def test_deactivate_self_wrong_password(session, verified_user):
    """Raises 401 when password is incorrect."""
    with pytest.raises(HTTPException) as exc:
        await UserService.deactivate_self(session, verified_user, "wrongpassword")
    assert exc.value.status_code == 401


async def test_deactivate_self_sets_inactive(session, verified_user):
    """Sets is_active=False on success."""
    await UserService.deactivate_self(session, verified_user, "TestPassword123!")

    await session.refresh(verified_user)
    assert verified_user.is_active is False


async def test_deactivate_self_revokes_tokens(session, verified_user):
    """Revokes all refresh tokens on success."""
    await TokenService.create_tokens(verified_user.email, verified_user.id, verified_user.role, session)

    await UserService.deactivate_self(session, verified_user, "TestPassword123!")

    active_tokens = await session.scalar(
        select(func.count()).select_from(RefreshToken).where(
            RefreshToken.user_id == verified_user.id,
            RefreshToken.revoked == False  # noqa: E712
        )
    )
    assert active_tokens == 0
