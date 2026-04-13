import pytest
from models.users import User
from models.addresses import Address
from utils.hashing import get_password_hash


@pytest.mark.asyncio
async def test_set_default_success(client, user_token, test_address):
    """POST /addresses/{id}/set-default returns 200 with is_default=true."""
    response = await client.post(
        f"/addresses/{test_address.id}/set-default",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    assert response.json()["is_default"] is True


@pytest.mark.asyncio
async def test_set_default_clears_previous(client, user_token, test_address):
    """Setting a new default clears the is_default flag on the previous default."""
    create_resp = await client.post(
        "/addresses/",
        json={"street": "2 Second St", "city": "Giza", "country": "Egypt", "postal_code": "12345"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    second_id = create_resp.json()["id"]

    await client.post(
        f"/addresses/{second_id}/set-default",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    old = await client.get(
        f"/addresses/{test_address.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert old.json()["is_default"] is False


@pytest.mark.asyncio
async def test_set_default_not_found(client, user_token):
    """POST /addresses/99999/set-default returns 404."""
    response = await client.post(
        "/addresses/99999/set-default",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_set_default_wrong_owner(client, user_token, session):
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

    response = await client.post(
        f"/addresses/{other_address.id}/set-default",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 404
