import pytest


# ─── Authentication (401) ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_category_requires_auth(client):
    response = await client.post("/admin/categories/", json={"name": "Books"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_category_requires_auth(client):
    response = await client.patch("/admin/categories/1", json={"name": "Books"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_category_requires_auth(client):
    response = await client.delete("/admin/categories/1")
    assert response.status_code == 401


# ─── Authorization (403) ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_category_forbidden_for_customer(client, user_token):
    response = await client.post(
        "/admin/categories/",
        json={"name": "Books"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_category_forbidden_for_customer(client, user_token, test_category):
    response = await client.patch(
        f"/admin/categories/{test_category.id}",
        json={"name": "Updated"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_category_forbidden_for_customer(client, user_token, test_category):
    response = await client.delete(
        f"/admin/categories/{test_category.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403