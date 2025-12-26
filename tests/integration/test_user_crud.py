import pytest
from models.users import User
from schemas.auth_schemas import CreateUserRequest
from services.auth_service import AuthService
from fastapi import BackgroundTasks, HTTPException


def test_create_user(session):
    """Test creating a user in the database."""
    
    user_data = CreateUserRequest(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="SecurePass123!",
        phone_number="+201111111111"
    )

    bg = BackgroundTasks()

    created_user = AuthService.create_user(user_data, session, bg)

    assert created_user.id is not None
    assert created_user.email == "test@example.com"
    assert created_user.first_name == "Test"
    assert created_user.is_verified is False

    db_user = session.query(User).filter(User.email == "test@example.com").first()
    assert db_user is not None
    assert db_user.email == created_user.email


def test_create_user_duplicate_email(session):
    """Test that duplicate email registration fails."""

    user_data = CreateUserRequest(
        email="duplicate@example.com",
        first_name="First",
        last_name="User",
        password="password123",
        phone_number="+201111111111"
    )
    bg = BackgroundTasks()
    
    AuthService.create_user(user_data, session, bg)
    
    with pytest.raises(HTTPException) as exc_info:
        AuthService.create_user(user_data, session, bg)
    
    assert exc_info.value.status_code == 400
    assert "already registered" in exc_info.value.detail.lower()


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
    assert  searched == None