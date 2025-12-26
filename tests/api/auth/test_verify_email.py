import pytest
from tests.conftest import session, client
from models.users import User
from datetime import datetime, timezone, timedelta, UTC

async def register_user(client, email, first_name="Test", last_name="User"):
    """Helper to register a user for testing."""
    await client.post("/auth/", json={
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "password": "SecurePass123!",
        "phone_number": "+201111111111"
    })

async def test_verify_email_success(client, session):
    """Test email verification happy path"""

    await register_user(client, "newuser@example.com")
    user = session.query(User).filter(User.email == "newuser@example.com").first()

    response = await client.post("/auth/verify", json={
        "email": "newuser@example.com",
        "code": user.verification_code
    })

    assert response.status_code == 200
    assert "verified successfully" in response.json()["message"].lower()
    
    session.refresh(user)
    assert user.is_verified is True
    assert user.verification_code is None



async def test_verify_email_invalid_code(client, session):
    """Test verification with invalid code fails"""

    await register_user(client, "invalid@example.com")
    user = session.query(User).filter(User.email == "invalid@example.com").first()

    response = await client.post("/auth/verify", json={
        "email": "invalid@example.com",
        "code": "000000" # This code will always be wrong
    })

    assert response.status_code == 400
    assert "invalid verification code" in response.json()["detail"].lower()



async def test_verify_email_expired_code(client, session):
    """Test verification with expired code fails"""

    await register_user(client, "expired@example.com")
    user = session.query(User).filter(User.email == "expired@example.com").first()
    user.verification_code_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    session.commit()

    response = await client.post("/auth/verify", json={
        "email": "expired@example.com",
        "code": user.verification_code
    })

    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()



async def test_verify_email_already_verified(client, session):
    """Test verifying an already verified email fails."""

    await register_user(client, "verified@example.com")
    user = session.query(User).filter(User.email == "verified@example.com").first()
    assert user is not None 
    user.is_verified = True
    session.commit()

    response = await client.post("/auth/verify", json={
        "email": "verified@example.com",
        "code": user.verification_code
    })

    assert response.status_code == 400
    assert "already verified" in response.json()["detail"].lower()


async def test_verify_email_non_existent_user(client, session):
    """Test verification for non-existent user fails."""

    response = await client.post("/auth/verify", json={
        "email": "non-existent@example.com",
        "code": "123456"
    })

    assert response.status_code == 404
    assert "user not found" in response.json()["detail"].lower()