import pytest
from schemas.auth import CreateUserRequest
from services.auth import AuthService
from fastapi import BackgroundTasks, HTTPException


def test_authenticate_user_success(session):
    """Test user authentication with correct credentials."""

    user_data = CreateUserRequest(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="SecurePass123!",
        phone_number="+201111111111"
    )

    bg = BackgroundTasks()

    created_user = AuthService.create_user(user_data, session, bg)
    created_user.is_verified = True
    session.commit()

    authenticated_user = AuthService.authenticate_user("test@example.com", "SecurePass123!", session)
    assert authenticated_user == created_user


def test_login_unverified_user(session):
    """Test that unverified users cannot authenticate."""

    user_data = CreateUserRequest(
        email="unverified_test@example.com",
        first_name="Test",
        last_name="User",
        password="SecurePass123!",
        phone_number="+201111111111"
    )

    bg = BackgroundTasks()

    created_user = AuthService.create_user(user_data, session, bg)

    with pytest.raises(HTTPException) as exc_info:
        authenticated_user = AuthService.authenticate_user("unverified_test@example.com", "SecurePass123!", session)

    assert exc_info.value.status_code == 403
    assert "email not verified" in exc_info.value.detail.lower()


def test_authenticate_user_wrong_password(session):
    """Test authentication fails with wrong password."""
    # Create verified user
    user_data = CreateUserRequest(
        email="wrong@example.com",
        first_name="Test",
        last_name="User",
        password="SecurePass123!",
        phone_number="+201111111111"
    )

    bg = BackgroundTasks()

    created_user = AuthService.create_user(user_data, session, bg)
    created_user.is_verified = True
    session.commit()

    # Attempt login with wrong password
    with pytest.raises(HTTPException) as exc_info:
        authenticated_user = AuthService.authenticate_user("wrong@example.com", "WRONGPASSWORD00", session)
    assert exc_info.value.status_code == 401


def test_login_inactive_user(session):
    """Test that deactivated users cannot authenticate."""

    user_data = CreateUserRequest(
        email="inactive_test@example.com",
        first_name="Test",
        last_name="User",
        password="SecurePass123!",
        phone_number="+201111111111"
    )

    bg = BackgroundTasks()

    created_user = AuthService.create_user(user_data, session, bg)
    created_user.is_verified = True
    created_user.is_active = False
    session.commit()

    # Attempt login
    with pytest.raises(HTTPException) as exc_info:
        authenticated_user = AuthService.authenticate_user("inactive_test@example.com", "SecurePass123!", session)
    assert exc_info.value.status_code == 401
