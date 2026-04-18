import pytest
from models.users import User
from models.addresses import Address
from utils.hashing import get_password_hash


@pytest.mark.asyncio
async def test_update_address_success(client, user_token, test_address):
    """PATCH /addresses/{id} returns 200 with the updated field value."""
    response = await client.patch(
        f"/addresses/{test_address.id}",
        json={"city": "Alexandria"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    assert response.json()["city"] == "Alexandria"


@pytest.mark.asyncio
async def test_update_address_partial(client, user_token, test_address):
    """Updating only one field leaves other fields unchanged."""
    response = await client.patch(
        f"/addresses/{test_address.id}",
        json={"city": "Alexandria"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    data = response.json()
    assert data["city"] == "Alexandria"
    assert data["street"] == test_address.street
    assert data["country"] == test_address.country


@pytest.mark.asyncio
async def test_update_address_set_default(client, user_token, test_address):
    """Setting is_default=true on a second address clears the first default."""
    create_resp = await client.post(
        "/addresses/",
        json={"street": "2 Second St", "city": "Giza", "country": "Egypt", "postal_code": "12345"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    second_id = create_resp.json()["id"]

    await client.patch(
        f"/addresses/{second_id}",
        json={"is_default": True},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    old = await client.get(
        f"/addresses/{test_address.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert old.json()["is_default"] is False


@pytest.mark.asyncio
async def test_update_address_not_found(client, user_token):
    """PATCH /addresses/99999 returns 404."""
    response = await client.patch(
        "/addresses/99999",
        json={"city": "Cairo"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_address_wrong_owner(client, user_token, session):
    """Returns 404 when attempting to update another user's address."""
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

    response = await client.patch(
        f"/addresses/{other_address.id}",
        json={"city": "Cairo"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_address_empty_body(client, user_token, test_address):
    """Sending an empty body returns 422 (model_validator requires at least one field)."""
    response = await client.patch(
        f"/addresses/{test_address.id}",
        json={},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 422
