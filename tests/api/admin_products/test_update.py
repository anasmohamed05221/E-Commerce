import pytest


@pytest.mark.asyncio
async def test_update_product_success(client, admin_token, product_factory):
    """Admin updates a product — returns 200 with updated fields."""
    product = product_factory(name="Old Name", price=100.00, stock=5)

    response = await client.patch(
        f"/admin/products/{product.id}",
        json={"name": "New Name", "price": "200.00"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert float(data["price"]) == 200.00
    assert data["stock"] == 5  # unchanged


@pytest.mark.asyncio
async def test_update_product_not_found(client, admin_token):
    """Returns 404 for a non-existent product."""
    response = await client.patch(
        "/admin/products/99999",
        json={"name": "Ghost"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_product_invalid_category(client, admin_token, product_factory):
    """Returns 404 when the new category_id does not exist."""
    product = product_factory()
    response = await client.patch(
        f"/admin/products/{product.id}",
        json={"category_id": 99999},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_product_empty_body(client, admin_token, product_factory):
    """Returns 422 when body has no fields (model_validator rejects it)."""
    product = product_factory()
    response = await client.patch(
        f"/admin/products/{product.id}",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_product_negative_price(client, admin_token, product_factory):
    """Returns 422 when price is negative."""
    product = product_factory()
    response = await client.patch(
        f"/admin/products/{product.id}",
        json={"price": "-5.00"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422
