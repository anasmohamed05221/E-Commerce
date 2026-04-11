import pytest
from fastapi import HTTPException
from models.categories import Category
from services.categories import CategoryService, CACHE_KEY
from core.redis_client import redis_client


@pytest.mark.asyncio
async def test_create_category_success(session):
    category = await CategoryService.create_category(session, name="Books", description="All books")

    assert category.id is not None
    assert category.name == "Books"
    assert category.description == "All books"
    redis_client.redis.delete.assert_called_once_with(CACHE_KEY)


@pytest.mark.asyncio
async def test_create_category_without_description(session):
    category = await CategoryService.create_category(session, name="Books", description=None)

    assert category.id is not None
    assert category.description is None


@pytest.mark.asyncio
async def test_create_category_duplicate_name_raises_409(session):
    await CategoryService.create_category(session, name="Books", description=None)

    with pytest.raises(HTTPException) as exc:
        await CategoryService.create_category(session, name="Books", description=None)

    assert exc.value.status_code == 409
