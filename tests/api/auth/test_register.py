from tests.conftest import session, client
from models.users import User
import pytest
from datetime import datetime, UTC, timezone

async def test_register_success(client, session):
    """Test successful user registration."""
    response = await client.post("/auth/", json={
        "email": "newuser@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "SecurePass123!",
        "phone_number": "+201111111111"
    })
    assert response.status_code == 201
    assert "Registration successful" in response.json()["message"]

    # Verify user in DB
    user = session.query(User).filter(User.email == "newuser@example.com").first()
    assert user is not None
    assert user.is_verified is False

    # Verify verification code is set
    assert user.verification_code is not None
    assert user.verification_code_expires_at is not None
    assert user.verification_code_expires_at.replace(tzinfo=timezone.utc) > datetime.now(UTC)


async def test_register_duplicate(client, session):
    """Test duplicate email registration is declined."""
    response = await client.post("/auth/", json={
        "email": "duplicateuser@example.com",
        "first_name": "Duplicate",
        "last_name": "User",
        "password": "SecurePass123!",
        "phone_number": "+201111111111"
    })
    response_2 = await client.post("/auth/", json={
        "email": "duplicateuser@example.com",
        "first_name": "Duplicate",
        "last_name": "User",
        "password": "SecurePass123!",
        "phone_number": "+201111111111"
    })

    assert response_2.status_code == 400
    
    # Verify it's not duplicated in DB
    users = session.query(User).filter(User.email == "duplicateuser@example.com").all()
    assert len(users) == 1


async def test_register_email_case_insensitive(client, session):
    """Test that email is case-insensitive."""
    await client.post("/auth/", json={
        "email": "CaseSensitive@Example.COM",
        "first_name": "Case",
        "last_name": "Sensetive",
        "password": "SecurePass123!",
        "phone_number": "+201111111111"
    })
    
    response = await client.post("/auth/", json={
        "email": "casesensitive@example.com",  # Same email, different case
        "first_name": "Case",
        "last_name": "Sensetive",
        "password": "SecurePass123!",
        "phone_number": "+201111111111"
    })
    
    assert response.status_code == 400  # Should be treated as duplicate


async def test_register_invalid_email(client, session):
    """Test invalid email format is declined."""
    response = await client.post("/auth/", json={
        "email": "@incorrectemail.wrong",
        "first_name": "Incorrect",
        "last_name": "Email",
        "password": "SecurePass123!",
        "phone_number": "+201111111111"
    })

    assert response.status_code == 422

    # Verify it's not added to DB
    user = session.query(User).filter(User.email == "@incorrectemail.wrong").first()
    assert user is None



async def test_register_missing_fields(client, session):
    """Test registration with missing fields is declined."""
    response = await client.post("/auth/", json={
        "email": "missingfields@email.com",
        "first_name": "Missing",
        "last_name": "Fields",
        "password": "SecurePass123!"
    })

    assert response.status_code == 422

    # Verify it's not added to DB
    user = session.query(User).filter(User.email == "missingfields@email.com").first()
    assert user is None



async def test_register_weak_password(client, session):
    """Test registration with a weak password is declined."""
    response = await client.post("/auth/", json={
        "email": "weakpassword@email.com",
        "first_name": "Weak",
        "last_name": "Password",
        "password": "wp",
        "phone_number": "+201111111111"
    })

    assert response.status_code == 422

    # Verify it's not added to DB
    user = session.query(User).filter(User.email == "weakpassword@email.com").first()
    assert user is None




async def test_register_extremely_long_email(client, session):
    """Test that extremely long emails are rejected."""
    long_email = "a" * 300 + "@example.com"  # 300+ chars
    
    response = await client.post("/auth/", json={
        "email": long_email,
        "first_name": "Long",
        "last_name": "Email",
        "password": "SecurePass123!",
        "phone_number": "+201111111111"
    })
    

    assert response.status_code == 422



async def test_register_unicode_names(client, session):
    """Test that Unicode characters in names are supported."""
    response = await client.post("/auth/", json={
        "email": "unicode@example.com",
        "first_name": "José",
        "last_name": "محمد",  # Arabic characters
        "password": "SecurePass123!",
        "phone_number": "+201111111111"
    })
    
    assert response.status_code == 201
    
    user = session.query(User).filter(User.email == "unicode@example.com").first()
    assert user.first_name == "José"
    assert user.last_name == "محمد"



async def test_register_email_with_whitespace(client, session):
    """Test that leading/trailing whitespace in email is stripped."""
    response = await client.post("/auth/", json={
        "email": "  whitespace@example.com  ",
        "first_name": "White",
        "last_name": "Space",
        "password": "SecurePass123!",
        "phone_number": "+201111111111"
    })
    
    assert response.status_code == 201
    
    # Verify it's stored without whitespace
    user = session.query(User).filter(User.email == "whitespace@example.com").first()
    assert user is not None
    assert user.email == "whitespace@example.com"  # No spaces