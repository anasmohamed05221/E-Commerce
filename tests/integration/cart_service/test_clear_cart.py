import pytest
from models.cart_items import CartItem
from models.users import User
from services.cart import CartService
from utils.hashing import get_password_hash


def test_clear_cart_removes_all_items(session, verified_user, product_factory):
    """All cart items for the user are deleted after clear_cart."""
    p1 = product_factory(name="Laptop", stock=10)
    p2 = product_factory(name="Mouse", price=50.00, stock=5)
    CartService.add_to_cart(session, verified_user.id, p1.id, 1)
    CartService.add_to_cart(session, verified_user.id, p2.id, 2)

    CartService.clear_cart(session, verified_user.id)

    count = session.query(CartItem).filter(CartItem.user_id == verified_user.id).count()
    assert count == 0


def test_clear_cart_empty_cart_is_idempotent(session, verified_user):
    """Clearing an already-empty cart succeeds without raising any error."""
    CartService.clear_cart(session, verified_user.id)

    count = session.query(CartItem).filter(CartItem.user_id == verified_user.id).count()
    assert count == 0


def test_clear_cart_only_removes_own_items(session, verified_user, product_factory):
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
    session.commit()
    session.refresh(other_user)

    product = product_factory(stock=10)
    CartService.add_to_cart(session, verified_user.id, product.id, 1)
    CartService.add_to_cart(session, other_user.id, product.id, 1)

    CartService.clear_cart(session, verified_user.id)

    own_count = session.query(CartItem).filter(CartItem.user_id == verified_user.id).count()
    other_count = session.query(CartItem).filter(CartItem.user_id == other_user.id).count()
    assert own_count == 0
    assert other_count == 1
