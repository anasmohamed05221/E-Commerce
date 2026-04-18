import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from services.products import ProductService
from schemas.products import ProductUpdate
from models.categories import Category


async def test_update_product_success(session, product_factory):
    """Only provided fields are updated; unprovided fields remain unchanged."""
    product = await product_factory(name="Old Name", price=100.00, stock=5)

    body = ProductUpdate(name="New Name", price=200.00)
    updated = await ProductService.update_product(session, body, product.id)

    assert updated.name == "New Name"
    assert float(updated.price) == 200.00
    assert updated.stock == 5  # unchanged


async def test_update_product_category(session, product_factory):
    """category_id can be updated to a valid category."""
    product = await product_factory()
    new_category = Category(name="Accessories", description="Accessories")
    session.add(new_category)
    await session.commit()
    await session.refresh(new_category)

    body = ProductUpdate(category_id=new_category.id)
    updated = await ProductService.update_product(session, body, product.id)

    assert updated.category.id == new_category.id


async def test_update_product_not_found(session):
    """Raises 404 when product_id does not exist."""
    body = ProductUpdate(name="Ghost")

    with pytest.raises(HTTPException) as exc:
        await ProductService.update_product(session, body, 99999)

    assert exc.value.status_code == 404


async def test_update_product_invalid_category(session, product_factory):
    """Raises 404 when the new category_id does not exist."""
    product = await product_factory()
    body = ProductUpdate(category_id=99999)

    with pytest.raises(HTTPException) as exc:
        await ProductService.update_product(session, body, product.id)

    assert exc.value.status_code == 404


def test_update_product_empty_body():
    """Sending all-None body raises ValidationError."""
    with pytest.raises(ValidationError):
        ProductUpdate()
