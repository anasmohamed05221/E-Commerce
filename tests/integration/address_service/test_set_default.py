import pytest
from fastapi import HTTPException
from models.users import User
from services.addresses import AddressService
from schemas.addresses import AddressCreate
from utils.hashing import get_password_hash


async def test_set_default_success(session, verified_user, test_address):
    """Returns the address with is_default=True."""
    result = await AddressService.set_default(session, verified_user.id, test_address.id)

    assert result.is_default is True
    assert result.id == test_address.id


async def test_set_default_clears_previous_default(session, verified_user, test_address):
    """Previous default loses is_default flag when a new default is set."""
    second_data = AddressCreate(street="789 New St", city="Giza", country="Egypt", postal_code="12345")
    second = await AddressService.create_address(session, verified_user.id, second_data)

    await AddressService.set_default(session, verified_user.id, second.id)

    await session.refresh(test_address)
    await session.refresh(second)
    assert test_address.is_default is False
    assert second.is_default is True


async def test_set_default_not_found(session, verified_user):
    """Raises 404 for a non-existent address ID."""
    with pytest.raises(HTTPException) as exc:
        await AddressService.set_default(session, verified_user.id, 99999)

    assert exc.value.status_code == 404


async def test_set_default_wrong_owner(session, verified_user):
    """Raises 404 when the address belongs to a different user."""
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

    data = AddressCreate(street="1 Other St", city="Alexandria", country="Egypt", postal_code="21500")
    other_address = await AddressService.create_address(session, other_user.id, data)

    with pytest.raises(HTTPException) as exc:
        await AddressService.set_default(session, verified_user.id, other_address.id)

    assert exc.value.status_code == 404
