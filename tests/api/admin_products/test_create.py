import pytest


@pytest.mark.asyncio
async def test_create_product_success(client, admin_token, test_category):
    """Admin creates a product — returns 201 with full ProductDetailOut shape."""
    response = await client.post(
        "/admin/products/",
        json={
            "name": "Laptop",
            "price": "999.99",
            "stock": 10,
            "category_id": test_category.id,
            "description": "A great laptop",
            "image_url": "http://example.com/laptop.jpg"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Laptop"
    assert float(data["price"]) == 999.99
    assert data["stock"] == 10
    assert data["description"] == "A great laptop"
    assert "category" in data
    assert data["category"]["id"] == test_category.id
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_product_invalid_category(client, admin_token):
    """Returns 404 when category_id does not exist."""
    response = await client.post(
        "/admin/products/",
        json={"name": "Ghost", "price": "10.00", "stock": 1, "category_id": 99999},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_product_missing_required_fields(client, admin_token):
    """Returns 422 when required fields are missing."""
    response = await client.post(
        "/admin/products/",
        json={"name": "Incomplete"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_product_negative_price(client, admin_token, test_category):
    """Returns 422 when price is negative."""
    response = await client.post(
        "/admin/products/",
        json={"name": "Bad", "price": "-1.00", "stock": 1, "category_id": test_category.id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_product_negative_stock(client, admin_token, test_category):
    """Returns 422 when stock is negative."""
    response = await client.post(
        "/admin/products/",
        json={"name": "Bad", "price": "10.00", "stock": -1, "category_id": test_category.id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422
