import pytest
from models.users import User
from schemas.auth import CreateUserRequest
from services.auth import AuthService
from fastapi import BackgroundTasks


def test_get_user_by_email(session):
    """Test retrieving a user by email."""

    user_data = CreateUserRequest(
        email="find@example.com",
        first_name="Find",
        last_name="Me",
        password="password123",
        phone_number="+201234567890"
    )
    bg = BackgroundTasks()
    AuthService.create_user(user_data, session, bg)

    found_user = session.query(User).filter(User.email == "find@example.com").first()

    assert found_user is not None
    assert found_user.email == "find@example.com"
    assert found_user.first_name == "Find"
    assert found_user.last_name == "Me"


def test_deactivate_user(session):
    """Test deactivating a user account."""
    # Create user
    user_data = CreateUserRequest(
        email="deactivate@example.com",
        first_name="Test",
        last_name="User",
        password="password123",
        phone_number="+201111111111"
    )
    bg = BackgroundTasks()
    created_user = AuthService.create_user(user_data, session, bg)

    # Deactivate
    created_user.is_active = False
    session.commit()

    # Verify
    db_user = session.query(User).filter(User.id == created_user.id).first()
    assert db_user.is_active is False

    searched = AuthService.get_active_user_by_id(session, db_user.id)
    assert  searched is None
