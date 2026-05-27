import pytest
from fastapi import HTTPException
from models.users import User
from services.addresses import AddressService
from schemas.addresses import AddressCreate, AddressUpdate
from utils.hashing import get_password_hash


async def test_update_address_success(session, verified_user, test_address, test_tenant):
    """Updates a field and returns the address with the new value."""
    data = AddressUpdate(city="Alexandria")

    updated = await AddressService.update_address(session, tenant_id=test_tenant.id, user_id=verified_user.id, address_id=test_address.id, data=data)

    assert updated.city == "Alexandria"
    assert updated.street == test_address.street


async def test_update_address_set_default_clears_previous(session, verified_user, test_address, test_tenant):
    """Setting is_default=True on a second address clears the first default."""
    second_data = AddressCreate(street="789 New St", city="Giza", country="Egypt", postal_code="12345")
    second = await AddressService.create_address(session, tenant_id=test_tenant.id, user_id=verified_user.id, data=second_data)

    await AddressService.update_address(session, tenant_id=test_tenant.id, user_id=verified_user.id, address_id=second.id, data=AddressUpdate(is_default=True))

    await session.refresh(test_address)
    await session.refresh(second)
    assert test_address.is_default is False
    assert second.is_default is True


async def test_update_address_not_found(session, verified_user, test_tenant):
    """Raises 404 for a non-existent address ID."""
    with pytest.raises(HTTPException) as exc:
        await AddressService.update_address(session, tenant_id=test_tenant.id, user_id=verified_user.id, address_id=99999, data=AddressUpdate(city="X"))

    assert exc.value.status_code == 404


async def test_update_address_wrong_owner(session, verified_user, test_tenant):
    """Raises 404 when the address belongs to a different user."""
    other_user = User(
        tenant_id=test_tenant.id,
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
    other_address = await AddressService.create_address(session, tenant_id=test_tenant.id, user_id=other_user.id, data=data)

    with pytest.raises(HTTPException) as exc:
        await AddressService.update_address(session, tenant_id=test_tenant.id, user_id=verified_user.id, address_id=other_address.id, data=AddressUpdate(city="X"))

    assert exc.value.status_code == 404
