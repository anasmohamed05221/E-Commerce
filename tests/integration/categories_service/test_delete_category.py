import pytest
from fastapi import HTTPException
from models.categories import Category
from services.categories import CategoryService, CACHE_KEY
from core.redis_client import redis_client


@pytest.mark.asyncio
async def test_delete_category_success(session, test_category):
    await CategoryService.delete_category(session, test_category.id)

    gone = session.query(Category).filter(Category.id == test_category.id).first()
    assert gone is None
    redis_client.redis.delete.assert_called_once_with(CACHE_KEY)


@pytest.mark.asyncio
async def test_delete_category_not_found_raises_404(session):
    with pytest.raises(HTTPException) as exc:
        await CategoryService.delete_category(session, 99999)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_with_products_raises_409(session, test_category, product_factory):
    product_factory()  # creates a product linked to test_category

    with pytest.raises(HTTPException) as exc:
        await CategoryService.delete_category(session, test_category.id)

    assert exc.value.status_code == 409
