import pytest
from fastapi import HTTPException
from models.categories import Category
from services.categories import CategoryService, CACHE_KEY
from core.redis_client import redis_client


@pytest.mark.asyncio
async def test_update_category_name_success(session, test_category):
    updated = await CategoryService.update_category(
        session, test_category.id, name="Gadgets", description=None
    )

    assert updated.name == "Gadgets"
    assert updated.description == test_category.description  # unchanged
    redis_client.redis.delete.assert_called_once_with(CACHE_KEY)


@pytest.mark.asyncio
async def test_update_category_description_success(session, test_category):
    updated = await CategoryService.update_category(
        session, test_category.id, name=None, description="Updated description"
    )

    assert updated.description == "Updated description"
    assert updated.name == test_category.name  # unchanged
    redis_client.redis.delete.assert_called_once_with(CACHE_KEY)


@pytest.mark.asyncio
async def test_update_category_same_name_no_conflict(session, test_category):
    # Patching a category with its own name must not raise 409
    updated = await CategoryService.update_category(
        session, test_category.id, name=test_category.name, description=None
    )

    assert updated.name == test_category.name


@pytest.mark.asyncio
async def test_update_category_name_taken_by_other_raises_409(session, test_category):
    other = Category(name="Clothing", description=None)
    session.add(other)
    await session.commit()

    with pytest.raises(HTTPException) as exc:
        await CategoryService.update_category(
            session, test_category.id, name="Clothing", description=None
        )

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_update_category_not_found_raises_404(session):
    with pytest.raises(HTTPException) as exc:
        await CategoryService.update_category(session, 99999, name="X", description=None)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_category_no_fields_raises_400(session, test_category):
    with pytest.raises(HTTPException) as exc:
        await CategoryService.update_category(
            session, test_category.id, name=None, description=None
        )

    assert exc.value.status_code == 400
