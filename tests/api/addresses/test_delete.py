import pytest
from models.users import User
from models.addresses import Address
from utils.hashing import get_password_hash


@pytest.mark.asyncio
async def test_delete_address_success(client, user_token, test_address):
    """DELETE /addresses/{id} returns 204 with no body; subsequent GET returns 404."""
    response = await client.delete(
        f"/addresses/{test_address.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 204
    assert response.content == b""

    get_response = await client.get(
        f"/addresses/{test_address.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_address_not_found(client, user_token):
    """DELETE /addresses/99999 returns 404."""
    response = await client.delete(
        "/addresses/99999",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_address_wrong_owner(client, user_token, session):
    """Returns 404 when attempting to delete another user's address."""
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

    other_address = Address(
        user_id=other_user.id,
        street="1 Other St",
        city="Alexandria",
        country="Egypt",
        postal_code="21500",
        is_default=True
    )
    session.add(other_address)
    session.commit()

    response = await client.delete(
        f"/addresses/{other_address.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 404
