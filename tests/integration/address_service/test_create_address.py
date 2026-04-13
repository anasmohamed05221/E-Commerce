import pytest
from models.addresses import Address
from services.addresses import AddressService
from schemas.addresses import AddressCreate


def test_create_address_success(session, verified_user):
    """Creates an address with required fields and returns an Address with correct values."""
    data = AddressCreate(street="456 Other St", city="Alexandria", country="Egypt", postal_code="21500")

    address = AddressService.create_address(session, verified_user.id, data)

    assert address.id is not None
    assert address.user_id == verified_user.id
    assert address.street == "456 Other St"
    assert address.city == "Alexandria"
    assert address.country == "Egypt"
    assert address.postal_code == "21500"


def test_create_address_first_is_auto_default(session, verified_user):
    """First address becomes default even when is_default=False is explicitly passed."""
    data = AddressCreate(street="1 Main St", city="Cairo", country="Egypt", postal_code="11511", is_default=False)

    address = AddressService.create_address(session, verified_user.id, data)

    assert address.is_default is True


def test_create_address_explicit_default_clears_previous(session, verified_user, test_address):
    """Creating a new address with is_default=True clears the existing default."""
    assert test_address.is_default is True

    data = AddressCreate(street="789 New St", city="Giza", country="Egypt", postal_code="12345", is_default=True)
    AddressService.create_address(session, verified_user.id, data)

    session.refresh(test_address)
    assert test_address.is_default is False


def test_create_address_not_default_preserves_existing_default(session, verified_user, test_address):
    """Creating a non-default address does not affect the existing default."""
    data = AddressCreate(street="789 New St", city="Giza", country="Egypt", postal_code="12345", is_default=False)
    AddressService.create_address(session, verified_user.id, data)

    session.refresh(test_address)
    assert test_address.is_default is True


def test_create_address_optional_fields_saved(session, verified_user):
    """Label and state are persisted when provided."""
    data = AddressCreate(
        street="1 Home St", city="Cairo", country="Egypt", postal_code="11511",
        label="Home", state="Giza"
    )

    address = AddressService.create_address(session, verified_user.id, data)

    assert address.label == "Home"
    assert address.state == "Giza"
