from middleware.rate_limiter import limiter
from core.config import settings, Settings
from unittest.mock import patch
import os

def test_rate_limiter_disabled_in_testing():
    """Verify rate limiter is disabled during tests."""

    assert settings.ENV == "testing"
    assert limiter.enabled is False



async def test_can_make_multiple_requests_in_tests(client, verified_user):
    """Verify rate limiting doesn't interfere with tests."""
    # Make 10 login requests (normally limited to 5/min)
    for i in range(10):
        response = await client.post("/auth/token", data={
            "username": verified_user.email,
            "password": "TestPassword123!"
        })
        assert response.status_code == 200
