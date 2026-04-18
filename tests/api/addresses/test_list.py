import pytest
from models.users import User
from models.addresses import Address
from utils.hashing import get_password_hash


@pytest.mark.asyncio
async def test_list_addresses_success(client, user_token, test_address):
    """GET /addresses/ returns 200 with a list containing the user's addresses."""
    response = await client.get("/addresses/", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == test_address.id


@pytest.mark.asyncio
async def test_list_addresses_empty(client, user_token):
    """GET /addresses/ returns 200 with an empty list when user has no addresses."""
    response = await client.get("/addresses/", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_addresses_only_own(client, user_token, test_address, session):
    """Addresses belonging to other users are not included in the response."""
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

    response = await client.get("/addresses/", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 200
    ids = [a["id"] for a in response.json()]
    assert test_address.id in ids
    assert other_address.id not in ids
