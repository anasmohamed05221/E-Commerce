import pytest


@pytest.mark.asyncio
async def test_deactivate_user_success(client, admin_token, verified_user):
    """Returns 200 with is_active=false on the response."""
    response = await client.patch(
        f"/admin/users/{verified_user.id}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    assert data["id"] == verified_user.id


@pytest.mark.asyncio
async def test_deactivate_user_not_found(client, admin_token):
    """Returns 404 for a non-existent user."""
    response = await client.patch(
        "/admin/users/99999/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deactivate_user_self(client, admin_token, verified_admin):
    """Returns 400 when admin targets their own account."""
    response = await client.patch(
        f"/admin/users/{verified_admin.id}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_deactivate_user_already_inactive(client, admin_token, session, verified_user):
    """Returns 409 when user is already inactive."""
    verified_user.is_active = False
    session.commit()

    response = await client.patch(
        f"/admin/users/{verified_user.id}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409
