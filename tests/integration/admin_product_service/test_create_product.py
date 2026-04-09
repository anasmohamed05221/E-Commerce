import pytest
from fastapi import HTTPException
from services.products import ProductService
from schemas.products import ProductCreate


def test_create_product_success(session, test_category):
    """Product is persisted and returned with category eagerly loaded."""
    body = ProductCreate(
        name="Laptop",
        price=999.99,
        stock=10,
        category_id=test_category.id,
        description="A great laptop",
        image_url="http://example.com/laptop.jpg"
    )

    product = ProductService.create_product(session, body)

    assert product.id is not None
    assert product.name == "Laptop"
    assert float(product.price) == 999.99
    assert product.stock == 10
    assert product.description == "A great laptop"
    assert product.category is not None
    assert product.category.id == test_category.id


def test_create_product_invalid_category(session):
    """Raises 404 when category_id does not exist."""
    body = ProductCreate(name="Ghost", price=10.00, stock=1, category_id=99999)

    with pytest.raises(HTTPException) as exc:
        ProductService.create_product(session, body)

    assert exc.value.status_code == 404


def test_create_product_minimal_fields(session, test_category):
    """Optional fields default to None when not provided."""
    body = ProductCreate(name="Basic", price=5.00, stock=0, category_id=test_category.id)

    product = ProductService.create_product(session, body)

    assert product.description is None
    assert product.image_url is None
