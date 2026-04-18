import pytest
from models.categories import Category
@pytest.mark.asyncio
async def test_get_categories_success(client, session):
    """Test getting a list of categories via the endpoint."""
    # 1. Setup data
    c1 = Category(name="Electronics", description="Tech gear")
    c2 = Category(name="Books", description="Reading material")
    session.add_all([c1, c2])
    await session.commit()
    # 2. Action: Hit the endpoint
    response = await client.get("/categories/")
    # 3. Assertions
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    
    # Verify sorting translated perfectly to JSON
    assert data[0]["name"] == "Books"
    assert data[1]["name"] == "Electronics"
    # Verify the description isn't getting filtered out by Pydantic
    assert data[0]["description"] == "Reading material"
@pytest.mark.asyncio
async def test_get_categories_empty(client):
    """Test getting categories when none exist."""
    response = await client.get("/categories/")
    
    assert response.status_code == 200
    data = response.json()
    assert data == []