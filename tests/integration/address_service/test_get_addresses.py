import pytest
from models.users import User
from services.addresses import AddressService
from schemas.addresses import AddressCreate
from utils.hashing import get_password_hash


async def test_get_addresses_returns_all(session, verified_user, test_address):
    """Returns all addresses belonging to the user."""
    data = AddressCreate(street="789 Second St", city="Giza", country="Egypt", postal_code="12345")
    await AddressService.create_address(session, verified_user.id, data)

    addresses = await AddressService.get_addresses(session, verified_user.id)

    assert len(addresses) == 2


async def test_get_addresses_empty(session, verified_user):
    """Returns an empty list when the user has no addresses."""
    addresses = await AddressService.get_addresses(session, verified_user.id)

    assert addresses == []


async def test_get_addresses_excludes_other_users(session, verified_user, test_address):
    """Does not return addresses belonging to a different user."""
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
    await AddressService.create_address(session, other_user.id, data)

    addresses = await AddressService.get_addresses(session, verified_user.id)

    assert len(addresses) == 1
    assert addresses[0].user_id == verified_user.id
