import pytest


@pytest.mark.asyncio
async def test_get_user_success(client, admin_token, verified_user):
    """Returns 200 with correct AdminUserOut shape."""
    response = await client.get(
        f"/admin/users/{verified_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == verified_user.id
    assert data["email"] == verified_user.email
    assert "role" in data
    assert "is_active" in data
    assert "is_verified" in data


@pytest.mark.asyncio
async def test_get_user_not_found(client, admin_token):
    """Returns 404 for a non-existent user."""
    response = await client.get(
        "/admin/users/99999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
