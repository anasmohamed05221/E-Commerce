import pytest


# ─── Authentication (401) ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_product_requires_auth(client):
    """POST /admin/products/ returns 401 without a token."""
    response = await client.post("/admin/products/", json={
        "name": "Laptop", "price": "999.99", "stock": 10, "category_id": 1
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_product_requires_auth(client):
    """PATCH /admin/products/{id} returns 401 without a token."""
    response = await client.patch("/admin/products/1", json={"name": "New"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_product_requires_auth(client):
    """DELETE /admin/products/{id} returns 401 without a token."""
    response = await client.delete("/admin/products/1")
    assert response.status_code == 401


# ─── Authorization (403) ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_product_forbidden_for_customer(client, user_token, test_category):
    """Customer role is rejected with 403."""
    response = await client.post(
        "/admin/products/",
        json={"name": "Laptop", "price": "999.99", "stock": 10, "category_id": test_category.id},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_product_forbidden_for_customer(client, user_token, product_factory):
    """Customer role is rejected with 403."""
    product = await product_factory()
    response = await client.patch(
        f"/admin/products/{product.id}",
        json={"name": "New"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_product_forbidden_for_customer(client, user_token, product_factory):
    """Customer role is rejected with 403."""
    product = await product_factory()
    response = await client.delete(
        f"/admin/products/{product.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
