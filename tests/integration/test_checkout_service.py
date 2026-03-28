import pytest
from fastapi import HTTPException
from services.checkout import CheckoutService
from services.cart import CartService
from models.cart_items import CartItem
from models.inventory_changes import InventoryChange


def test_checkout_success(session, verified_user, product_factory):
    """Full checkout flow creates order, decrements stock, logs inventory change, and clears cart."""
    product = product_factory(name="Laptop", price=1000.00, stock=10)
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=2)

    order = CheckoutService.checkout(db=session, user_id=verified_user.id)
    # Order created with correct total
    assert order is not None
    assert order.user_id == verified_user.id
    assert float(order.total_amount) == 2000.00
    assert order.status == "pending"
    # Order items created with price snapshot
    items = order.items
    assert len(items) == 1
    assert items[0].product_id == product.id
    assert items[0].quantity == 2
    assert float(items[0].price_at_time) == 1000.00
    assert float(items[0].subtotal) == 2000.0
    # Stock decremented
    session.refresh(product)
    assert product.stock == 8
    # Inventory change recorded
    inv_change = session.query(InventoryChange).filter(InventoryChange.product_id==product.id).first()
    assert inv_change is not None
    assert inv_change.change_amount == -2
    assert inv_change.reason == "sale"
    # Cart cleared
    cart_items = session.query(CartItem).filter(CartItem.user_id==verified_user.id).all()
    assert len(cart_items) == 0
    

def test_checkout_cart_empty(session, verified_user):
    """Checkout with no cart items raises 400."""
    with pytest.raises(HTTPException) as exc:
        order = CheckoutService.checkout(db=session, user_id=verified_user.id)
    assert exc.value.status_code == 400
    assert exc.value.detail == "Can't checkout while cart is empty"


def test_checkout_stock_insufficient(session, verified_user, product_factory):
    """Checkout raises 409 when a cart item quantity exceeds current stock."""
    product = product_factory(name="Laptop", price=1000.00, stock=10)
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=2)
    product.stock = 1
    session.commit()
    with pytest.raises(HTTPException) as exc:
        order = CheckoutService.checkout(db=session, user_id=verified_user.id)
    assert exc.value.status_code == 409
    assert exc.value.detail["message"] == "Not enough stock available"


def test_checkout_multiple_cart_items(session, verified_user, product_factory):
    """Checkout with multiple products creates all order items and clears the full cart."""
    product1 = product_factory(name="Laptop", price=1000.00, stock=10)
    product2 = product_factory(name="Monitor", price=500.00, stock=7)
    product3 = product_factory(name="Keyboard", price=60.00, stock=5)
    
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product1.id, quantity=2)
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product2.id, quantity=1)
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product3.id, quantity=3)

    order = CheckoutService.checkout(db=session, user_id=verified_user.id)
    # Order created with correct total
    assert order is not None
    assert order.user_id == verified_user.id
    assert float(order.total_amount) == 2680.00
    assert order.status == "pending"
    # Order items created
    assert len(order.items) == 3
    # Stock decremented for all 3 products
    session.refresh(product1)
    session.refresh(product2)
    session.refresh(product3)
    assert product1.stock == 8
    assert product2.stock == 6
    assert product3.stock == 2
    # Inventory change recorded for each product
    inv_change1 = session.query(InventoryChange).filter(InventoryChange.product_id==product1.id).first()
    inv_change2 = session.query(InventoryChange).filter(InventoryChange.product_id==product2.id).first()
    inv_change3 = session.query(InventoryChange).filter(InventoryChange.product_id==product3.id).first()
    assert inv_change1 is not None
    assert inv_change1.change_amount == -2
    assert inv_change1.reason == "sale"
    assert inv_change2 is not None
    assert inv_change2.change_amount == -1
    assert inv_change2.reason == "sale"
    assert inv_change3 is not None
    assert inv_change3.change_amount == -3
    assert inv_change3.reason == "sale"

    # Cart cleared
    cart_items = session.query(CartItem).filter(CartItem.user_id==verified_user.id).all()
    assert len(cart_items) == 0


def test_checkout_stock_equivalent(session, verified_user, product_factory):
    """Checkout succeeds when quantity exactly matches available stock, leaving stock at zero."""
    product = product_factory(name="Laptop", price=1000.00, stock=10)
    
    CartService.add_to_cart(db=session, user_id=verified_user.id, product_id=product.id, quantity=10)

    order = CheckoutService.checkout(db=session, user_id=verified_user.id)

    # Order created correctly
    assert order is not None
    assert order.user_id == verified_user.id
    assert float(order.total_amount) == 10000.00
    assert order.status == "pending"
    # Stock hits exactly zero
    session.refresh(product)
    assert product.stock == 0