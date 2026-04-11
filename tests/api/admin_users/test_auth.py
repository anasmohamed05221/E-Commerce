import pytest


# ─── 401 Unauthenticated ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_users_requires_auth(client):
    """GET /admin/users/ returns 401 without a token."""
    response = await client.get("/admin/users/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_user_requires_auth(client):
    """GET /admin/users/{id} returns 401 without a token."""
    response = await client.get("/admin/users/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_deactivate_user_requires_auth(client):
    """PATCH /admin/users/{id}/deactivate returns 401 without a token."""
    response = await client.patch("/admin/users/1/deactivate")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_reactivate_user_requires_auth(client):
    """PATCH /admin/users/{id}/reactivate returns 401 without a token."""
    response = await client.patch("/admin/users/1/reactivate")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_role_requires_auth(client):
    """PATCH /admin/users/{id}/role returns 401 without a token."""
    response = await client.patch("/admin/users/1/role", json={"role": "admin"})
    assert response.status_code == 401


# ─── 403 Forbidden (customer) ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_users_forbidden_for_customer(client, user_token):
    """Customer role is rejected with 403."""
    response = await client.get("/admin/users/", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_user_forbidden_for_customer(client, user_token):
    """Customer role is rejected with 403."""
    response = await client.get("/admin/users/1", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_deactivate_user_forbidden_for_customer(client, user_token):
    """Customer role is rejected with 403."""
    response = await client.patch("/admin/users/1/deactivate", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_reactivate_user_forbidden_for_customer(client, user_token):
    """Customer role is rejected with 403."""
    response = await client.patch("/admin/users/1/reactivate", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_role_forbidden_for_customer(client, user_token):
    """Customer role is rejected with 403."""
    response = await client.patch("/admin/users/1/role", json={"role": "admin"}, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403
