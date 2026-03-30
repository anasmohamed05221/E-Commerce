import pytest
from models.categories import Category
from models.products import Product
from services.products import ProductService

def test_get_products_with_pagination(session):
    """Test that ProductService.get_products respects limit and calculates total correctly."""
    # 1. Setup: Create testing data directly in the database
    category = Category(name="Electronics", description="Tech gear")
    session.add(category)
    session.commit()
    session.refresh(category)
    # Create 3 products
    p1 = Product(name="Laptop", price=1000.00, stock=5, category_id=category.id)
    p2 = Product(name="Mouse", price=50.00, stock=20, category_id=category.id)
    p3 = Product(name="Keyboard", price=80.00, stock=10, category_id=category.id)
    session.add_all([p1, p2, p3])
    session.commit()

    # 2. Action: Call the service directly (limit=2, offset=0)
    items, total = ProductService.get_products(
        db=session,
        limit=2,
        offset=0,
        category_id=None,
        min_price=None,
        max_price=None
    )

    # 3. Assertions
    assert total == 3
    assert len(items) == 2
    assert items[0].name == "Laptop"
    assert items[1].name == "Mouse"