import pytest
from sqlalchemy import select
from fastapi import HTTPException
from models.addresses import Address
from models.users import User
from services.addresses import AddressService
from schemas.addresses import AddressCreate
from utils.hashing import get_password_hash


async def test_delete_address_success(session, verified_user, test_address):
    """Address is removed from the database after deletion."""
    address_id = test_address.id

    await AddressService.delete_address(session, verified_user.id, address_id)

    result = await session.scalar(select(Address).where(Address.id == address_id))
    assert result is None


async def test_delete_address_not_found(session, verified_user):
    """Raises 404 for a non-existent address ID."""
    with pytest.raises(HTTPException) as exc:
        await AddressService.delete_address(session, verified_user.id, 99999)

    assert exc.value.status_code == 404


async def test_delete_address_wrong_owner(session, verified_user):
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
        await AddressService.delete_address(session, verified_user.id, other_address.id)

    assert exc.value.status_code == 404
