import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_api_get_products_list(client: AsyncClient, seed_products):
    """Test public access to product list"""
    response = await client.get("/products/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_api_get_product_by_id_success(client: AsyncClient, seed_products):
    """Test retrieving a single product by ID"""
    target_product = seed_products[0]
    
    response = await client.get(f"/products/{target_product.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify exact data and nested category
    assert data["id"] == target_product.id
    assert data["name"] == target_product.name
    assert "category" in data
    assert data["category"]["name"] == "Electronics"


@pytest.mark.asyncio
async def test_api_get_product_not_found(client: AsyncClient):
    """Test 404 handling for non-existent product"""
    # Random ID that doesn't exist
    response = await client.get("/products/9999")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


@pytest.mark.asyncio
async def test_api_get_products_with_filters(client: AsyncClient, seed_products):
    """Test filtering products by price."""
    
    # We seeded a Laptop ($1000) and a Mouse ($50).
    # Filtering for max_price=100 should strictly return only the Mouse.
    response = await client.get("/products/?max_price=100")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Mouse"


@pytest.mark.asyncio
async def test_api_get_products_invalid_price_range(client: AsyncClient, seed_products):
    """Test validation when min_price > max_price."""
    
    response = await client.get("/products/?min_price=500&max_price=100")
    
    assert response.status_code == 422
    assert "min_price must be less than or equal to max_price" in response.json()["detail"]