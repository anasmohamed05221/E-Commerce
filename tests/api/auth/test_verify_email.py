import pytest
from tests.conftest import session, client
from tests.api.auth.test_register import test_register_success

async def test_verify_email_success(client, session):
    """Test verifying email successfully"""
    user = test_register_success(clent, session)

    response = await clien.post("/auth/verify", json={
        "email": user.email,
        "code": user.verification_code
    })

    assert response.status_code == 200
    assert user.is_verified == True