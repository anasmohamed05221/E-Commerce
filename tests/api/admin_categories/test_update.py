import pytest


@pytest.mark.asyncio
async def test_update_category_name_success(client, admin_token, test_category):
    response = await client.patch(
        f"/admin/categories/{test_category.id}",
        json={"name": "Gadgets"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Gadgets"
    assert data["description"] == test_category.description  # unchanged


@pytest.mark.asyncio
async def test_update_category_description_success(client, admin_token, test_category):
    response = await client.patch(
        f"/admin/categories/{test_category.id}",
        json={"description": "Updated description"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"
    assert data["name"] == test_category.name  # unchanged


@pytest.mark.asyncio
async def test_update_category_not_found_returns_404(client, admin_token):
    response = await client.patch(
        "/admin/categories/99999",
        json={"name": "Ghost"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_category_name_taken_returns_409(client, admin_token, test_category):
    # Create a second category, then try to rename test_category to its name
    await client.post(
        "/admin/categories/",
        json={"name": "Clothing"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    response = await client.patch(
        f"/admin/categories/{test_category.id}",
        json={"name": "Clothing"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_category_no_fields_returns_400(client, admin_token, test_category):
    response = await client.patch(
        f"/admin/categories/{test_category.id}",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 400