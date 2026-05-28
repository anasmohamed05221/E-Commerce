import pytest
from models.categories import Category
from services.categories import CategoryService

@pytest.mark.asyncio
async def test_get_categories_sorting(session, test_tenant):
    """Test that CategoryService.get_categories sorts alphabetically."""
    # 1. Setup: Create testing data strictly out of alphabetical order
    c1 = Category(tenant_id=test_tenant.id, name="Mugs", description="Mugs here")
    c2 = Category(tenant_id=test_tenant.id, name="Apparel", description="Shirts and stuff")
    c3 = Category(tenant_id=test_tenant.id, name="Zebra", description="Animal stuff")
    session.add_all([c1, c2, c3])
    await session.commit()
    # 2. Action: Call the service directly
    categories = await CategoryService.get_categories(db=session, tenant_id=test_tenant.id)
    # 3. Assertions
    assert len(categories) == 3
    # A comes before M, M comes before Z
    assert categories[0].name == "Apparel"
    assert categories[1].name == "Mugs"
    assert categories[2].name == "Zebra"

@pytest.mark.asyncio
async def test_get_categories_empty(session, test_tenant):
    """Test that CategoryService.get_categories returns an empty list when DB is empty."""
    categories = await CategoryService.get_categories(db=session, tenant_id=test_tenant.id)
    assert categories == []
