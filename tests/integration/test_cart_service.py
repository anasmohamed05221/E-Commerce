import pytest
from decimal import Decimal
from fastapi import HTTPException
from models.users import User
from models.categories import Category
from models.products import Product
from models.cart_items import CartItem
from services.cart import CartService
from utils.hashing import get_password_hash


def create_test_user(session) -> User:
    user = User(
        email="cartuser@test.com",
        first_name="Cart",
        last_name="Tester",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201234567890",
        is_verified=True,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_test_product(session, *, name="Laptop", price=1000.00, stock=10) -> Product:
    category = session.query(Category).first()
    if not category:
        category = Category(name="Electronics", description="Tech gear")
        session.add(category)
        session.commit()
        session.refresh(category)

    product = Product(name=name, price=price, stock=stock, category_id=category.id)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product



def test_get_cart_empty(session):
    """Empty cart returns an empty list."""
    user = create_test_user(session)

    cart_items = CartService.get_cart(db=session, user_id=user.id)

    assert cart_items == []


def test_get_cart_returns_items_with_product_loaded(session):
    """Cart items are returned with the product relationship eagerly loaded."""
    user = create_test_user(session)
    product = create_test_product(session)
    CartService.add_to_cart(db=session, user_id=user.id, product_id=product.id, quantity=2)

    cart_items = CartService.get_cart(db=session, user_id=user.id)

    assert len(cart_items) == 1
    assert cart_items[0].product_id == product.id
    assert cart_items[0].quantity == 2
    assert cart_items[0].product is not None
    assert cart_items[0].product.name == "Laptop"




def test_calculate_total_price_empty_cart():
    """Total price of an empty cart is zero."""
    total = CartService.calculate_cart_total_price([])

    assert total == Decimal("0")


def test_calculate_total_price_multiple_items(session):
    """Total price sums (price * quantity) across all items."""
    user = create_test_user(session)
    p1 = create_test_product(session, name="Laptop", price=1000.00, stock=10)
    p2 = create_test_product(session, name="Mouse", price=50.00, stock=20)
    CartService.add_to_cart(db=session, user_id=user.id, product_id=p1.id, quantity=2)
    CartService.add_to_cart(db=session, user_id=user.id, product_id=p2.id, quantity=3)

    cart_items = CartService.get_cart(db=session, user_id=user.id)
    total = CartService.calculate_cart_total_price(cart_items)

    # (1000 * 2) + (50 * 3) = 2150
    assert total == Decimal("2150.00")


def test_add_to_cart_new_item(session):
    """Adding a product creates a new cart item with correct quantity."""
    user = create_test_user(session)
    product = create_test_product(session)

    cart_item = CartService.add_to_cart(db=session, user_id=user.id, product_id=product.id, quantity=3)

    assert cart_item.user_id == user.id
    assert cart_item.product_id == product.id
    assert cart_item.quantity == 3
    assert cart_item.product is not None


def test_add_to_cart_increments_existing_item(session):
    """Adding the same product again increments quantity instead of duplicating."""
    user = create_test_user(session)
    product = create_test_product(session, stock=10)
    CartService.add_to_cart(db=session, user_id=user.id, product_id=product.id, quantity=3)

    cart_item = CartService.add_to_cart(db=session, user_id=user.id, product_id=product.id, quantity=4)

    assert cart_item.quantity == 7
    # Only one row exists for this user+product
    count = session.query(CartItem).filter_by(user_id=user.id, product_id=product.id).count()
    assert count == 1


def test_add_to_cart_product_not_found(session):
    """Adding a non-existent product raises 404."""
    user = create_test_user(session)

    with pytest.raises(HTTPException) as exc:
        CartService.add_to_cart(db=session, user_id=user.id, product_id=9999, quantity=1)

    assert exc.value.status_code == 404


def test_add_to_cart_exceeds_stock_new_item(session):
    """Adding quantity greater than stock raises 409."""
    user = create_test_user(session)
    product = create_test_product(session, stock=5)

    with pytest.raises(HTTPException) as exc:
        CartService.add_to_cart(db=session, user_id=user.id, product_id=product.id, quantity=6)

    assert exc.value.status_code == 409
    assert exc.value.detail["available_stock"] == 5


def test_add_to_cart_exceeds_stock_on_increment(session):
    """Incrementing quantity past stock raises 409."""
    user = create_test_user(session)
    product = create_test_product(session, stock=5)
    CartService.add_to_cart(db=session, user_id=user.id, product_id=product.id, quantity=3)

    with pytest.raises(HTTPException) as exc:
        CartService.add_to_cart(db=session, user_id=user.id, product_id=product.id, quantity=3)

    assert exc.value.status_code == 409
    assert exc.value.detail["available_stock"] == 5



def test_update_cart_item_success(session):
    """Updating quantity sets the new value correctly."""
    user = create_test_user(session)
    product = create_test_product(session, stock=10)
    CartService.add_to_cart(db=session, user_id=user.id, product_id=product.id, quantity=2)

    cart_item = CartService.update_cart_item(db=session, user_id=user.id, product_id=product.id, new_quantity=5)

    assert cart_item.quantity == 5
    assert cart_item.product is not None


def test_update_cart_item_not_found(session):
    """Updating a non-existent cart item raises 404."""
    user = create_test_user(session)
    product = create_test_product(session)

    with pytest.raises(HTTPException) as exc:
        CartService.update_cart_item(db=session, user_id=user.id, product_id=product.id, new_quantity=1)

    assert exc.value.status_code == 404


def test_update_cart_item_exceeds_stock(session):
    """Updating quantity beyond stock raises 409."""
    user = create_test_user(session)
    product = create_test_product(session, stock=5)
    CartService.add_to_cart(db=session, user_id=user.id, product_id=product.id, quantity=2)

    with pytest.raises(HTTPException) as exc:
        CartService.update_cart_item(db=session, user_id=user.id, product_id=product.id, new_quantity=6)

    assert exc.value.status_code == 409
    assert exc.value.detail["available_stock"] == 5



def test_remove_from_cart_success(session):
    """Removing an item deletes it from the database."""
    user = create_test_user(session)
    product = create_test_product(session)
    CartService.add_to_cart(db=session, user_id=user.id, product_id=product.id, quantity=1)

    CartService.remove_from_cart(db=session, user_id=user.id, product_id=product.id)

    remaining = session.query(CartItem).filter_by(user_id=user.id).count()
    assert remaining == 0


def test_remove_from_cart_not_found(session):
    """Removing a non-existent cart item raises 404."""
    user = create_test_user(session)

    with pytest.raises(HTTPException) as exc:
        CartService.remove_from_cart(db=session, user_id=user.id, product_id=9999)

    assert exc.value.status_code == 404
