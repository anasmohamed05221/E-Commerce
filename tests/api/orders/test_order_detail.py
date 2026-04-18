import pytest
from models.users import User
from models.addresses import Address
from models.enums import PaymentMethod
from utils.hashing import get_password_hash
from services.cart import CartService
from services.checkout import CheckoutService


@pytest.mark.asyncio
async def test_get_order_success(client, user_token, order_factory):
    """Returns 200 with full OrderOut shape including nested items and product."""
    order = await order_factory()

    response = await client.get(
        f"/orders/{order.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order.id
    assert "total_amount" in data
    assert "status" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert len(data["items"]) > 0
    item = data["items"][0]
    assert "price_at_time" in item
    assert "quantity" in item
    assert "subtotal" in item
    assert "product" in item
    assert "name" in item["product"]


@pytest.mark.asyncio
async def test_get_order_not_found(client, user_token):
    """Returns 404 for a non-existent order."""
    response = await client.get("/orders/99999", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_order_other_user(client, user_token, session, product_factory):
    """Returns 404 when the order belongs to a different user."""
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

    addr = Address(user_id=other_user.id, street="1 St", city="Cairo", country="Egypt", postal_code="11511", is_default=True)
    session.add(addr)
    await session.commit()

    product = await product_factory()
    await CartService.add_to_cart(session, other_user.id, product.id, 1)
    other_order = await CheckoutService.checkout(db=session, user_id=other_user.id, address_id=addr.id, payment_method=PaymentMethod.COD)

    response = await client.get(
        f"/orders/{other_order.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404