import pytest
from models.users import User
from utils.hashing import get_password_hash


@pytest.fixture
def test_user(session):
    """Create a verified user for token tests."""
    user = User(
        email="token_test@example.com",
        first_name="Token",
        last_name="Test",
        hashed_password=get_password_hash("password123"),
        phone_number="+201111111111",
        is_verified=True,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
