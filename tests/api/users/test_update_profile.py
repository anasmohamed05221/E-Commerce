import pytest


@pytest.mark.asyncio
async def test_update_profile_requires_auth(client):
    """PATCH /users/me requires authentication."""
    response = await client.patch("/users/me", json={"first_name": "Test"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile_success(client, user_token):
    """Returns 200 with the updated field value."""
    response = await client.patch(
        "/users/me",
        json={"first_name": "Updated"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"


@pytest.mark.asyncio
async def test_update_profile_partial_update(client, user_token, verified_user):
    """Only the provided field changes; others retain their original values."""
    response = await client.patch(
        "/users/me",
        json={"last_name": "Smith"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    data = response.json()
    assert data["last_name"] == "Smith"
    assert data["first_name"] == verified_user.first_name
    assert data["email"] == verified_user.email


@pytest.mark.asyncio
async def test_update_profile_invalid_phone(client, user_token):
    """An invalid phone number format returns 422."""
    response = await client.patch(
        "/users/me",
        json={"phone_number": "not-a-phone"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_profile_empty_body(client, user_token):
    """An empty body returns 422 (model_validator requires at least one field)."""
    response = await client.patch(
        "/users/me",
        json={},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_profile_response_schema(client, user_token):
    """Response contains all expected UserOut fields and no sensitive data."""
    response = await client.patch(
        "/users/me",
        json={"first_name": "Schema"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "first_name" in data
    assert "last_name" in data
    assert "phone_number" in data
    assert "hashed_password" not in data
