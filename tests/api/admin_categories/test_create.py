import pytest


@pytest.mark.asyncio
async def test_create_category_success(client, admin_token):
    response = await client.post(
        "/admin/categories/",
        json={"name": "Books", "description": "All kinds of books"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Books"
    assert data["description"] == "All kinds of books"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_category_without_description(client, admin_token):
    response = await client.post(
        "/admin/categories/",
        json={"name": "Books"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 201
    assert response.json()["description"] is None


@pytest.mark.asyncio
async def test_create_category_duplicate_name_returns_409(client, admin_token, test_category):
    response = await client.post(
        "/admin/categories/",
        json={"name": test_category.name},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_category_missing_name_returns_422(client, admin_token):
    response = await client.post(
        "/admin/categories/",
        json={"description": "No name provided"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 422