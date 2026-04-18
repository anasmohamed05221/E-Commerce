import pytest
from sqlalchemy import select, func
from models.cart_items import CartItem
from models.users import User
from services.cart import CartService
from utils.hashing import get_password_hash


async def test_clear_cart_removes_all_items(session, verified_user, product_factory):
    """All cart items for the user are deleted after clear_cart."""
    p1 = await product_factory(name="Laptop", stock=10)
    p2 = await product_factory(name="Mouse", price=50.00, stock=5)
    await CartService.add_to_cart(session, verified_user.id, p1.id, 1)
    await CartService.add_to_cart(session, verified_user.id, p2.id, 2)

    await CartService.clear_cart(session, verified_user.id)

    count = await session.scalar(
        select(func.count()).select_from(CartItem).where(CartItem.user_id == verified_user.id)
    )
    assert count == 0


async def test_clear_cart_empty_cart_is_idempotent(session, verified_user):
    """Clearing an already-empty cart succeeds without raising any error."""
    await CartService.clear_cart(session, verified_user.id)

    count = await session.scalar(
        select(func.count()).select_from(CartItem).where(CartItem.user_id == verified_user.id)
    )
    assert count == 0


async def test_clear_cart_only_removes_own_items(session, verified_user, product_factory):
    """Only the requesting user's cart items are deleted; other users' items are unaffected."""
    other_user = User(
        email="other@example.com",
        first_name="Other",
        last_name="User",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111112",
        is_verified=True,
        is_active=True
    )
    session.add(other_user)
    await session.commit()
    await session.refresh(other_user)

    product = await product_factory(stock=10)
    await CartService.add_to_cart(session, verified_user.id, product.id, 1)
    await CartService.add_to_cart(session, other_user.id, product.id, 1)

    await CartService.clear_cart(session, verified_user.id)

    own_count = await session.scalar(
        select(func.count()).select_from(CartItem).where(CartItem.user_id == verified_user.id)
    )
    other_count = await session.scalar(
        select(func.count()).select_from(CartItem).where(CartItem.user_id == other_user.id)
    )
    assert own_count == 0
    assert other_count == 1
