import pytest


@pytest.mark.asyncio
async def test_reactivate_user_success(client, admin_token, session, verified_user):
    """Returns 200 with is_active=true on the response."""
    verified_user.is_active = False
    session.commit()

    response = await client.patch(
        f"/admin/users/{verified_user.id}/reactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True
    assert data["id"] == verified_user.id


@pytest.mark.asyncio
async def test_reactivate_user_not_found(client, admin_token):
    """Returns 404 for a non-existent user."""
    response = await client.patch(
        "/admin/users/99999/reactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reactivate_user_already_active(client, admin_token, verified_user):
    """Returns 409 when user is already active."""
    response = await client.patch(
        f"/admin/users/{verified_user.id}/reactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409
