import pytest


@pytest.mark.asyncio
async def test_delete_category_success(client, admin_token, test_category):
    response = await client.delete(
        f"/admin/categories/{test_category.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 204
    assert response.content == b""


@pytest.mark.asyncio
async def test_delete_category_not_found_returns_404(client, admin_token):
    response = await client.delete(
        "/admin/categories/99999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_with_products_returns_409(client, admin_token, test_category, product_factory):
    await product_factory()  # creates a product linked to test_category

    response = await client.delete(
        f"/admin/categories/{test_category.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 409