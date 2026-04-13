import pytest
from fastapi import HTTPException
from services.orders import OrderService
from services.cart import CartService
from services.checkout import CheckoutService
from models.users import User
from models.addresses import Address
from models.inventory_changes import InventoryChange
from models.enums import OrderStatus, InventoryChangeReason, PaymentMethod
from utils.hashing import get_password_hash


def test_cancel_order_success(session, verified_user, order_factory):
    """Cancellation sets status to CANCELLED, restores stock, and logs an inventory change."""
    created_order = order_factory()

    cancelled_order = OrderService.cancel_order(session, verified_user.id, created_order.id)
    assert cancelled_order.status == OrderStatus.CANCELLED

    product = cancelled_order.items[0].product
    session.refresh(product)
    assert product.stock == 10

    inv_change = session.query(InventoryChange).filter(
        InventoryChange.product_id == product.id
    ).order_by(InventoryChange.id.desc()).first()
    assert inv_change.change_amount == 2
    assert inv_change.reason.value == "cancellation"


def test_cancel_order_multiple_items(session, verified_user, order_factory, product_factory):
    """Stock is restored and inventory changes are logged for every item in the order, not just the first."""
    p1 = product_factory(name="Laptop", stock=10)
    p2 = product_factory(name="Mouse", price=50.00, stock=5)
    order = order_factory([(p1, 2), (p2, 3)])

    OrderService.cancel_order(session, verified_user.id, order.id)

    session.refresh(p1)
    session.refresh(p2)
    assert p1.stock == 10
    assert p2.stock == 5

    inv_p1 = session.query(InventoryChange).filter(
        InventoryChange.product_id == p1.id
    ).order_by(InventoryChange.id.desc()).first()
    inv_p2 = session.query(InventoryChange).filter(
        InventoryChange.product_id == p2.id
    ).order_by(InventoryChange.id.desc()).first()
    assert inv_p1.change_amount == 2
    assert inv_p1.reason.value == "cancellation"
    assert inv_p2.change_amount == 3
    assert inv_p2.reason.value == "cancellation"


def test_cancel_order_not_found(session, verified_user):
    """Raises 404 when the order does not exist."""
    with pytest.raises(HTTPException) as exc:
        OrderService.cancel_order(session, verified_user.id, 99)
    assert exc.value.status_code == 404


def test_cancel_order_wrong_owner(session, verified_user, product_factory):
    """Raises 404 when the order exists but belongs to a different user."""
    other_user = User(
        email="other2@example.com",
        first_name="Other",
        last_name="User",
        hashed_password=get_password_hash("TestPassword123!"),
        phone_number="+201111111113",
        is_verified=True,
        is_active=True
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    addr = Address(user_id=other_user.id, street="1 St", city="Cairo", country="Egypt", postal_code="11511", is_default=True)
    session.add(addr)
    session.commit()

    product = product_factory()
    CartService.add_to_cart(session, other_user.id, product.id, 1)
    other_order = CheckoutService.checkout(db=session, user_id=other_user.id, address_id=addr.id, payment_method=PaymentMethod.COD)

    with pytest.raises(HTTPException) as exc:
        OrderService.cancel_order(session, verified_user.id, other_order.id)
    assert exc.value.status_code == 404


def test_cancel_order_already_cancelled(session, verified_user, order_factory):
    """Raises 409 when attempting to cancel an order that is already cancelled."""
    order = order_factory()
    OrderService.cancel_order(session, verified_user.id, order.id)

    with pytest.raises(HTTPException) as exc:
        OrderService.cancel_order(session, verified_user.id, order.id)
    assert exc.value.status_code == 409
