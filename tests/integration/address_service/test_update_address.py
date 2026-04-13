import pytest
from fastapi import HTTPException
from models.users import User
from services.addresses import AddressService
from schemas.addresses import AddressCreate, AddressUpdate
from utils.hashing import get_password_hash


def test_update_address_success(session, verified_user, test_address):
    """Updates a field and returns the address with the new value."""
    data = AddressUpdate(city="Alexandria")

    updated = AddressService.update_address(session, verified_user.id, test_address.id, data)

    assert updated.city == "Alexandria"
    assert updated.street == test_address.street


def test_update_address_set_default_clears_previous(session, verified_user, test_address):
    """Setting is_default=True on a second address clears the first default."""
    second_data = AddressCreate(street="789 New St", city="Giza", country="Egypt", postal_code="12345")
    second = AddressService.create_address(session, verified_user.id, second_data)

    AddressService.update_address(session, verified_user.id, second.id, AddressUpdate(is_default=True))

    session.refresh(test_address)
    session.refresh(second)
    assert test_address.is_default is False
    assert second.is_default is True


def test_update_address_not_found(session, verified_user):
    """Raises 404 for a non-existent address ID."""
    with pytest.raises(HTTPException) as exc:
        AddressService.update_address(session, verified_user.id, 99999, AddressUpdate(city="X"))

    assert exc.value.status_code == 404


def test_update_address_wrong_owner(session, verified_user):
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
    session.commit()
    session.refresh(other_user)

    data = AddressCreate(street="1 Other St", city="Alexandria", country="Egypt", postal_code="21500")
    other_address = AddressService.create_address(session, other_user.id, data)

    with pytest.raises(HTTPException) as exc:
        AddressService.update_address(session, verified_user.id, other_address.id, AddressUpdate(city="X"))

    assert exc.value.status_code == 404
