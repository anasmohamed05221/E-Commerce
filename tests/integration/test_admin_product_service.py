import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from services.products import ProductService
from services.cart import CartService
from services.checkout import CheckoutService
from schemas.products import ProductCreate, ProductUpdate
from models.products import Product
from models.cart_items import CartItem


# ─── create_product ───────────────────────────────────────────────────────────


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


# ─── update_product ───────────────────────────────────────────────────────────


def test_update_product_success(session, product_factory):
    """Only provided fields are updated; unprovided fields remain unchanged."""
    product = product_factory(name="Old Name", price=100.00, stock=5)

    body = ProductUpdate(name="New Name", price=200.00)
    updated = ProductService.update_product(session, body, product.id)

    assert updated.name == "New Name"
    assert float(updated.price) == 200.00
    assert updated.stock == 5  # unchanged


def test_update_product_category(session, product_factory):
    """category_id can be updated to a valid category."""
    from models.categories import Category

    product = product_factory()
    new_category = Category(name="Accessories", description="Accessories")
    session.add(new_category)
    session.commit()
    session.refresh(new_category)

    body = ProductUpdate(category_id=new_category.id)
    updated = ProductService.update_product(session, body, product.id)

    assert updated.category.id == new_category.id


def test_update_product_not_found(session):
    """Raises 404 when product_id does not exist."""
    body = ProductUpdate(name="Ghost")

    with pytest.raises(HTTPException) as exc:
        ProductService.update_product(session, body, 99999)

    assert exc.value.status_code == 404


def test_update_product_invalid_category(session, product_factory):
    """Raises 404 when the new category_id does not exist."""
    product = product_factory()
    body = ProductUpdate(category_id=99999)

    with pytest.raises(HTTPException) as exc:
        ProductService.update_product(session, body, product.id)

    assert exc.value.status_code == 404


def test_update_product_empty_body():
    """Sending all-None body raises ValidationError."""
    with pytest.raises(ValidationError) as exc:
        body = ProductUpdate()



# ─── delete_product ───────────────────────────────────────────────────────────


def test_delete_product_success(session, product_factory):
    """Product is removed from the database after deletion."""
    product = product_factory()
    product_id = product.id

    ProductService.delete_product(session, product_id)

    assert session.query(Product).filter(Product.id == product_id).first() is None


def test_delete_product_not_found(session):
    """Raises 404 when product_id does not exist."""
    with pytest.raises(HTTPException) as exc:
        ProductService.delete_product(session, 99999)

    assert exc.value.status_code == 404


def test_delete_product_blocked_by_order(session, verified_user, product_factory):
    """Raises 409 when the product is referenced by an existing order item."""
    product = product_factory()
    CartService.add_to_cart(session, verified_user.id, product.id, 1)
    CheckoutService.checkout(session, verified_user.id)

    with pytest.raises(HTTPException) as exc:
        ProductService.delete_product(session, product.id)

    assert exc.value.status_code == 409


def test_delete_product_removes_cart_items(session, verified_user, product_factory):
    """Deleting a product that is only in a cart (no orders) succeeds and cascades cart items."""
    product = product_factory()
    CartService.add_to_cart(session, verified_user.id, product.id, 2)

    cart_item = session.query(CartItem).filter(CartItem.product_id == product.id).first()
    assert cart_item is not None

    ProductService.delete_product(session, product.id)

    assert session.query(CartItem).filter(CartItem.product_id == product.id).first() is None
    assert session.query(Product).filter(Product.id == product.id).first() is None