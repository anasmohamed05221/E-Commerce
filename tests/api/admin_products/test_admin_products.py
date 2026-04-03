import pytest
from services.cart import CartService
from services.checkout import CheckoutService


# ─── Authentication ───────────────────────────────────────────────────────────


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


# ─── Authorization ────────────────────────────────────────────────────────────


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
    product = product_factory()
    response = await client.patch(
        f"/admin/products/{product.id}",
        json={"name": "New"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_product_forbidden_for_customer(client, user_token, product_factory):
    """Customer role is rejected with 403."""
    product = product_factory()
    response = await client.delete(
        f"/admin/products/{product.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


# ─── POST /admin/products/ ────────────────────────────────────────────────────


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


# ─── PATCH /admin/products/{id} ───────────────────────────────────────────────


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


# ─── DELETE /admin/products/{id} ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_product_success(client, admin_token, product_factory):
    """Admin deletes a product — returns 204 with no body."""
    product = product_factory()

    response = await client.delete(
        f"/admin/products/{product.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 204
    assert response.content == b""


@pytest.mark.asyncio
async def test_delete_product_not_found(client, admin_token):
    """Returns 404 for a non-existent product."""
    response = await client.delete(
        "/admin/products/99999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_product_blocked_by_order(client, admin_token, verified_user, session, product_factory):
    """Returns 409 when the product is referenced by an order item."""
    product = product_factory()
    CartService.add_to_cart(session, verified_user.id, product.id, 1)
    CheckoutService.checkout(session, verified_user.id)

    response = await client.delete(
        f"/admin/products/{product.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_product_with_cart_item_succeeds(client, admin_token, verified_user, session, product_factory):
    """Returns 204 when product is in a cart but has no orders — cart item is cascade-deleted."""
    product = product_factory()
    CartService.add_to_cart(session, verified_user.id, product.id, 2)

    response = await client.delete(
        f"/admin/products/{product.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204
