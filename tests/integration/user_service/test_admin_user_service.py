import pytest
from fastapi import HTTPException
from models.users import User
from models.enums import UserRole
from models.refresh_tokens import RefreshToken

from services.users import UserService
from services.token import TokenService
from utils.hashing import get_password_hash


HASHED = get_password_hash("TestPassword123!")


def _make_user(session, email, role=UserRole.CUSTOMER, is_active=True):
    user = User(
        email=email,
        first_name="Test",
        last_name="User",
        hashed_password=HASHED,
        role=role,
        is_active=is_active,
        is_verified=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# ─── get_all_users ────────────────────────────────────────────────────────────

def test_get_all_users_empty(session):
    """Returns empty list and zero total when no users exist."""
    users, total = UserService.get_all_users(session, limit=10, offset=0, role_filter=None, is_active_filter=None)
    assert users == []
    assert total == 0


def test_get_all_users_returns_all(session, verified_user, verified_admin):
    """Returns all users regardless of role."""
    users, total = UserService.get_all_users(session, limit=10, offset=0, role_filter=None, is_active_filter=None)
    assert total == 2


def test_get_all_users_role_filter_customer(session, verified_user, verified_admin):
    """Returns only customers when role_filter=CUSTOMER."""
    users, total = UserService.get_all_users(session, limit=10, offset=0, role_filter=UserRole.CUSTOMER, is_active_filter=None)
    assert total == 1
    assert users[0].role == UserRole.CUSTOMER


def test_get_all_users_role_filter_admin(session, verified_user, verified_admin):
    """Returns only admins when role_filter=ADMIN."""
    users, total = UserService.get_all_users(session, limit=10, offset=0, role_filter=UserRole.ADMIN, is_active_filter=None)
    assert total == 1
    assert users[0].role == UserRole.ADMIN


def test_get_all_users_is_active_filter(session, verified_user):
    """Returns only inactive users when is_active_filter=False."""
    inactive = _make_user(session, "inactive@example.com", is_active=False)

    users, total = UserService.get_all_users(session, limit=10, offset=0, role_filter=None, is_active_filter=False)
    assert total == 1
    assert users[0].id == inactive.id


def test_get_all_users_pagination(session):
    """Limit and offset control the page; total reflects full count."""
    for i in range(3):
        _make_user(session, f"user{i}@example.com")

    users, total = UserService.get_all_users(session, limit=2, offset=0, role_filter=None, is_active_filter=None)
    assert total == 3
    assert len(users) == 2

    users_p2, total2 = UserService.get_all_users(session, limit=2, offset=2, role_filter=None, is_active_filter=None)
    assert total2 == 3
    assert len(users_p2) == 1


# ─── get_user_by_id ───────────────────────────────────────────────────────────

def test_get_user_by_id_found(session, verified_user):
    """Returns correct user when found."""
    user = UserService.get_user_by_id(session, verified_user.id)
    assert user.id == verified_user.id
    assert user.email == verified_user.email


def test_get_user_by_id_not_found(session):
    """Raises 404 for unknown user_id."""
    with pytest.raises(HTTPException) as exc:
        UserService.get_user_by_id(session, 99999)
    assert exc.value.status_code == 404


# ─── deactivate_user ──────────────────────────────────────────────────────────

def test_deactivate_user_self(session, verified_admin):
    """Raises 400 when admin targets themselves."""
    with pytest.raises(HTTPException) as exc:
        UserService.deactivate_user(session, verified_admin.id, verified_admin.id)
    assert exc.value.status_code == 400


def test_deactivate_user_already_inactive(session, verified_admin):
    """Raises 409 when user is already inactive."""
    inactive = _make_user(session, "inactive2@example.com", is_active=False)
    with pytest.raises(HTTPException) as exc:
        UserService.deactivate_user(session, inactive.id, verified_admin.id)
    assert exc.value.status_code == 409


def test_deactivate_user_sets_inactive(session, verified_admin, verified_user):
    """Sets is_active=False on the target user."""
    UserService.deactivate_user(session, verified_user.id, verified_admin.id)
    session.refresh(verified_user)
    assert verified_user.is_active is False


def test_deactivate_user_revokes_tokens(session, verified_admin, verified_user):
    """Revokes all refresh tokens of the target user."""
    TokenService.create_tokens(verified_user.email, verified_user.id, verified_user.role, session)

    UserService.deactivate_user(session, verified_user.id, verified_admin.id)

    active_tokens = session.query(RefreshToken).filter(
        RefreshToken.user_id == verified_user.id,
        RefreshToken.revoked == False  # noqa: E712
    ).count()
    assert active_tokens == 0


# ─── reactivate_user ──────────────────────────────────────────────────────────

def test_reactivate_user_already_active(session, verified_admin, verified_user):
    """Raises 409 when user is already active."""
    with pytest.raises(HTTPException) as exc:
        UserService.reactivate_user(session, verified_user.id)
    assert exc.value.status_code == 409


def test_reactivate_user_sets_active(session, verified_admin):
    """Sets is_active=True on a previously deactivated user."""
    inactive = _make_user(session, "inactive3@example.com", is_active=False)

    UserService.reactivate_user(session, inactive.id)

    session.refresh(inactive)
    assert inactive.is_active is True


# ─── update_user_role ─────────────────────────────────────────────────────────

def test_update_user_role_self(session, verified_admin):
    """Raises 400 when admin targets themselves."""
    with pytest.raises(HTTPException) as exc:
        UserService.update_user_role(session, verified_admin.id, UserRole.CUSTOMER, verified_admin.id)
    assert exc.value.status_code == 400


def test_update_user_role_same_role(session, verified_admin, verified_user):
    """Raises 409 when user already has the target role."""
    with pytest.raises(HTTPException) as exc:
        UserService.update_user_role(session, verified_user.id, UserRole.CUSTOMER, verified_admin.id)
    assert exc.value.status_code == 409


def test_update_user_role_promotes_to_admin(session, verified_admin, verified_user):
    """Promotes a customer to admin."""
    UserService.update_user_role(session, verified_user.id, UserRole.ADMIN, verified_admin.id)
    session.refresh(verified_user)
    assert verified_user.role == UserRole.ADMIN


def test_update_user_role_demotes_to_customer(session, verified_admin):
    """Demotes an admin to customer."""
    another_admin = _make_user(session, "admin2@example.com", role=UserRole.ADMIN)
    UserService.update_user_role(session, another_admin.id, UserRole.CUSTOMER, verified_admin.id)
    session.refresh(another_admin)
    assert another_admin.role == UserRole.CUSTOMER
