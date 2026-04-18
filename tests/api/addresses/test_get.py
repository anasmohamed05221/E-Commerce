import pytest
from models.users import User
from models.addresses import Address
from utils.hashing import get_password_hash


@pytest.mark.asyncio
async def test_get_address_success(client, user_token, test_address):
    """GET /addresses/{id} returns 200 with correct address data."""
    response = await client.get(
        f"/addresses/{test_address.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_address.id
    assert data["street"] == test_address.street
    assert data["city"] == test_address.city


@pytest.mark.asyncio
async def test_get_address_not_found(client, user_token):
    """GET /addresses/99999 returns 404 for a non-existent address."""
    response = await client.get("/addresses/99999", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_address_wrong_owner(client, user_token, session):
    """Returns 404 when the address belongs to a different user."""
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

    other_address = Address(
        user_id=other_user.id,
        street="1 Other St",
        city="Alexandria",
        country="Egypt",
        postal_code="21500",
        is_default=True
    )
    session.add(other_address)
    await session.commit()

    response = await client.get(
        f"/addresses/{other_address.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 404
